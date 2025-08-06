from config import SPREADSHEET_ID, SHEET_NAME, sheets_service


def append_to_sheet(data):
    body = {'values': [data]}
    sheets_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        body=body
    ).execute()