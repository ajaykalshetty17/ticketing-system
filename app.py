import os
import json
from google.oauth2 import service_account
import gspread

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

service_account_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT")

if not service_account_str:
    print("ERROR: GOOGLE_SERVICE_ACCOUNT not found")
    raise Exception("Missing GOOGLE_SERVICE_ACCOUNT environment variable")

try:
    service_account_info = json.loads(service_account_str)
except Exception as e:
    print("JSON LOAD ERROR:", str(e))
    raise

creds = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open("tickets").sheet1
