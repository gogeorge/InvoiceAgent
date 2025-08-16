from googleapiclient.http import MediaIoBaseDownload
import io
import pdfplumber
from config import FOLDER_ID, SPREADSHEET_ID, SHEET_NAME, drive_service, sheets_service

def download_pdf(file_id):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh

# === EXTRACT TEXT FROM PDF ===
def extract_text_from_pdf(file_bytes):
    with pdfplumber.open(file_bytes) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text() + '\n'
    return text