from invoice_monitor import check_expiring_invoices, generate_alert_message, send_notification

def test_monitor():
    """Test the invoice monitoring functionality"""
    print("Testing invoice monitoring...")
    
    # Check for expiring invoices
    expiring_invoices = check_expiring_invoices()
    
    # Generate and display alert
    alert_message = generate_alert_message(expiring_invoices)
    send_notification(alert_message)
    
    # Show detailed information for debugging
    print(f"\nFound {len(expiring_invoices)} expiring invoices:")
    for invoice in expiring_invoices:
        print(f"  - Invoice #{invoice['invoice_number']}: {invoice['client']} - {invoice['amount']} (expires in {invoice['days_until_expiry']} days)")

if __name__ == "__main__":
    test_monitor()
