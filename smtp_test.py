import os
import sys
import smtplib
from email.mime.text import MIMEText


def main():
    if len(sys.argv) < 2 and not os.getenv("EMAIL_RECIPIENTS"):
        print("Usage: python smtp_test.py recipient1[,recipient2,...]\n       or set EMAIL_RECIPIENTS env var")
        sys.exit(2)

    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    email_sender = os.getenv("EMAIL_SENDER")
    smtp_username = os.getenv("SMTP_USERNAME", email_sender)
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not email_sender:
        print("Missing EMAIL_SENDER")
        sys.exit(2)

    if len(sys.argv) >= 2:
        recipients = [addr.strip() for addr in sys.argv[1].split(",") if addr.strip()]
    else:
        recipients = [addr.strip() for addr in os.getenv("EMAIL_RECIPIENTS", "").split(",") if addr.strip()]

    subject = os.getenv("TEST_SUBJECT", "SMTP Test Message")
    body = os.getenv("TEST_BODY", "This is a test message from smtp_test.py")

    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = email_sender
    msg["To"] = ", ".join(recipients)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if os.getenv("SMTP_DEBUG") == "1":
                server.set_debuglevel(1)
            server.ehlo()
            if smtp_port == 587:
                server.starttls()
                server.ehlo()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            refused = server.sendmail(email_sender, recipients, msg.as_string())
            if refused:
                print(f"Some recipients were refused: {refused}")
            else:
                print(f"Email sent to: {', '.join(recipients)}")
    except smtplib.SMTPRecipientsRefused as e:
        print(f"SMTPRecipientsRefused: {e.recipients}")
        sys.exit(1)
    except smtplib.SMTPResponseException as e:
        try:
            error_text = e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
        except Exception:
            error_text = str(e.smtp_error)
        print(f"SMTPResponseException: {e.smtp_code} {error_text}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to send email: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


