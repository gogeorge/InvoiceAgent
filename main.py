import time
from gdrive_extract import download_pdf, extract_text_from_pdf
from ai_extract import extract_invoice_data
from append_sheet import append_to_sheet
from config import FOLDER_ID, drive_service

processed_files = set()
print("Starting the program...")

while True:
    print("Checking for new files...")
    results = drive_service.files().list(q=f"'{FOLDER_ID}' in parents and mimeType='application/pdf'",
                                         spaces='drive',
                                         fields="files(id, name)").execute()
    items = results.get('files', [])
    for item in items:
        if item['id'] not in processed_files:
            print(f"Processing {item['name']}...")
            pdf_file = download_pdf(item['id'])
            text = extract_text_from_pdf(pdf_file)
            client, date, amount, invoice_number, days = extract_invoice_data(text)
            if client and date and amount:
                append_to_sheet([invoice_number, client, date, amount, days])
                print(f"Added to sheet: Invoice #{invoice_number}, {client}, {date}, {amount}, {days} days")
            else:
                print("Failed to extract data.")
            processed_files.add(item['id'])
    time.sleep(60)