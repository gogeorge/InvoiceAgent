import datetime
import os
from email.utils import formatdate, make_msgid
from datetime import timedelta
import time
import re
import smtplib
from email.mime.text import MIMEText
from typing import List
from config import (
    sheets_service,
    SPREADSHEET_ID,
    SHEET_NAME,
    SMTP_SERVER,
    SMTP_PORT,
    EMAIL_SENDER,
    EMAIL_RECIPIENTS,
    SMTP_USERNAME,
    SMTP_PASSWORD,
)

def get_invoice_data():
    """Fetch all invoice data from the spreadsheet"""
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A:E'  # Assuming columns A-E are: Invoice Number, Client, Date, Amount, Days
        ).execute()
        
        values = result.get('values', [])
        if not values:
            print("No data found in spreadsheet")
            return []
        
        # Skip header row if it exists
        if values[0][0] == 'Invoice Number':
            values = values[1:]
        
        return values
    except Exception as e:
        print(f"Error fetching data from spreadsheet: {e}")
        return []

def _parse_date_flexible(date_str: str):
    """Try multiple common date formats and return a date or None."""
    if not date_str:
        return None
    date_str = date_str.strip()
    formats = (
        '%Y-%m-%d',  # 2025-07-31
        '%d/%m/%Y',  # 31/07/2025
        '%d-%m-%Y',  # 31-07-2025
        '%d.%m.%Y',  # 31.07.2025
        '%m/%d/%Y',  # 07/31/2025
    )
    for fmt in formats:
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

def calculate_expiry_date(invoice_date_str, days_str):
    """Calculate when an invoice payment expires with flexible parsing."""
    try:
        invoice_date = _parse_date_flexible(invoice_date_str)
        if not invoice_date:
            raise ValueError(f"unsupported date format: {invoice_date_str}")

        # Extract first integer found in days_str (handles '90', '90 days', etc.)
        if not days_str or days_str == "N/A":
            return None
        match = re.search(r"\d+", str(days_str))
        if not match:
            return None
        days = int(match.group(0))

        expiry_date = invoice_date + timedelta(days=days)
        return expiry_date
    except Exception as e:
        print(f"Error calculating expiry date for {invoice_date_str}, {days_str}: {e}")
        return None

def check_expiring_invoices():
    """Check for invoices expiring in the current week"""
    print("Checking for expiring invoices...")
    
    # Get current date and calculate week range
    today = datetime.date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday
    
    print(f"Checking invoices expiring between {start_of_week} and {end_of_week}")
    
    # Fetch invoice data
    invoices = get_invoice_data()
    
    expiring_invoices = []
    
    for invoice in invoices:
        if len(invoice) >= 5:  # Ensure we have all 5 columns
            invoice_number, client, date, amount, days = invoice
            
            expiry_date = calculate_expiry_date(date, days)
            if expiry_date and start_of_week <= expiry_date <= end_of_week:
                days_until_expiry = (expiry_date - today).days
                expiring_invoices.append({
                    'invoice_number': invoice_number,
                    'client': client,
                    'date': date,
                    'amount': amount,
                    'days': days,
                    'expiry_date': expiry_date,
                    'days_until_expiry': days_until_expiry
                })
    
    return expiring_invoices

def generate_alert_message(expiring_invoices):
    """Generate a message about expiring invoices"""
    if not expiring_invoices:
        return "✅ No invoices are expiring this week."
    
    message = "🚨 INVOICE PAYMENT ALERTS 🚨\n\n"
    message += f"Found {len(expiring_invoices)} invoice(s) expiring this week:\n\n"
    
    for invoice in expiring_invoices:
        urgency = "🔴 URGENT" if invoice['days_until_expiry'] <= 2 else "🟡 WARNING"
        message += f"{urgency} - Invoice #{invoice['invoice_number']}\n"
        message += f"   Client: {invoice['client']}\n"
        message += f"   Amount: {invoice['amount']}\n"
        message += f"   Expires: {invoice['expiry_date']} (in {invoice['days_until_expiry']} days)\n"
        message += f"   Original Date: {invoice['date']}\n\n"
    
    return message

def _send_email(subject: str, body: str, recipients: List[str]):
    """Send a plain-text email using configured SMTP settings."""
    if not EMAIL_SENDER or not recipients:
        print("Email not configured: missing EMAIL_SENDER or EMAIL_RECIPIENTS")
        return

    # Optionally strip emojis and non-ASCII to reduce spam filtering risk
    if os.environ.get("EMAIL_PLAIN") == "1":
        subject_to_send = subject.encode("ascii", "ignore").decode("ascii")
        body_to_send = body.encode("ascii", "ignore").decode("ascii")
    else:
        subject_to_send = subject
        body_to_send = body

    msg = MIMEText(body_to_send, _charset="utf-8")
    msg["Subject"] = subject_to_send
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(recipients)
    msg["Date"] = formatdate(localtime=True)
    try:
        msg["Message-ID"] = make_msgid(domain=EMAIL_SENDER.split("@")[-1])
    except Exception:
        msg["Message-ID"] = make_msgid()

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            if os.environ.get("SMTP_DEBUG") == "1":
                server.set_debuglevel(1)
            server.ehlo()
            if SMTP_PORT == 587:
                server.starttls()
                server.ehlo()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            refused = server.sendmail(EMAIL_SENDER, recipients, msg.as_string())
        if refused:
            print(f"Some recipients were refused: {refused}")
        else:
            print(f"Email sent to: {', '.join(recipients)}")
    except smtplib.SMTPRecipientsRefused as e:
        print(f"SMTPRecipientsRefused: {e.recipients}")
    except smtplib.SMTPResponseException as e:
        try:
            error_text = e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
        except Exception:
            error_text = str(e.smtp_error)
        print(f"SMTPResponseException: {e.smtp_code} {error_text}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_notification(message):
    """Send notification about expiring invoices"""
    print("\n" + "="*50)
    print(message)
    print("="*50 + "\n")

    subject = "Weekly Invoice Payment Alerts"
    _send_email(subject, message, EMAIL_RECIPIENTS)

def run_weekly_check():
    """Main function to run the weekly invoice check"""
    print(f"Starting weekly invoice check at {datetime.datetime.now()}")
    
    # Check if today is Monday
    today = datetime.date.today()
    if today.weekday() != 0:  # 0 = Monday
        print(f"Today is {today.strftime('%A')}, not Monday. Skipping check.")
        return
    
    # Check for expiring invoices
    expiring_invoices = check_expiring_invoices()
    
    # Generate and send alert
    alert_message = generate_alert_message(expiring_invoices)
    send_notification(alert_message)

def run_continuous_monitor():
    """Run the monitor continuously, checking every Monday"""
    print("Starting continuous invoice monitor...")
    print("Will check for expiring invoices every Monday at 9:00 AM")
    
    while True:
        now = datetime.datetime.now()
        
        # Check if it's Monday and around 9 AM
        if now.weekday() == 0 and now.hour == 9 and now.minute < 10:
            run_weekly_check()
            # Wait until next hour to avoid multiple runs
            time.sleep(3600)  # Sleep for 1 hour
        else:
            # Sleep for 1 hour and check again
            time.sleep(3600)

if __name__ == "__main__":
    # For testing, you can run a one-time check
    # run_weekly_check()
    
    # For production, run the continuous monitor
    run_continuous_monitor()
