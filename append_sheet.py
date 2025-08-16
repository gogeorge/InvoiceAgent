from config import SPREADSHEET_ID, SHEET_NAME, sheets_service


def append_to_sheet(data):
    # Check if the invoice number (first column) already exists in the sheet
    invoice_value = None
    if data and len(data) > 0:
        invoice_value = str(data[0]).strip()

    if invoice_value:
        existing_values_response = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:A"
        ).execute()

        existing_values = existing_values_response.get('values', [])
        existing_invoice_numbers = set()
        for row in existing_values:
            if not row:
                continue
            value = str(row[0]).strip()
            if value:
                existing_invoice_numbers.add(value)

        if invoice_value in existing_invoice_numbers:
            return  # Duplicate found; do not append

    body = {'values': [data]}
    sheets_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        body=body
    ).execute()