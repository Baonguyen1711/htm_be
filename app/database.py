from google.cloud import firestore
from google.oauth2 import service_account
from dotenv import load_dotenv
import os


load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Tạo Firestore client
def get_db():
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    db = firestore.Client(credentials=credentials)
    return db

db = get_db()
