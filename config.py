import openai
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables from local zsh env file
load_dotenv("env.invoiceagent.zsh", override=True)

# === CORE CONFIG (from environment) ===
FOLDER_ID = os.getenv('FOLDER_ID', '')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '')
SHEET_NAME = os.getenv('SHEET_NAME', 'Invoices')
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

# Validate required configuration early
_missing_vars = [name for name, value in (
    ('SPREADSHEET_ID', SPREADSHEET_ID),
    ('FOLDER_ID', FOLDER_ID),
) if not value]
if _missing_vars:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(_missing_vars)}. "
        "Set them in env.invoiceagent.zsh and reload (or source the file) before running."
    )

# Initialize OpenAI client with new API format
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# === GOOGLE API CLIENTS ===
# Prefer credentials from env var JSON; fall back to file path
_google_credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
if _google_credentials_json:
    creds = service_account.Credentials.from_service_account_info(
        json.loads(_google_credentials_json), scopes=SCOPES
    )
else:
    SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', 'service_account.json')
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

drive_service = build('drive', 'v3', credentials=creds)
sheets_service = build('sheets', 'v4', credentials=creds)

# === EMAIL (SMTP) SETTINGS ===
# Configure via environment variables to avoid hardcoding secrets
# Required env vars (recommended):
#   SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_RECIPIENTS, SMTP_USERNAME, SMTP_PASSWORD
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_RECIPIENTS = [addr.strip() for addr in os.getenv('EMAIL_RECIPIENTS', '').split(',') if addr.strip()]
SMTP_USERNAME = os.getenv('SMTP_USERNAME', EMAIL_SENDER)
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

