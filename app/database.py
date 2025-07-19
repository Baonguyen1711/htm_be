from google.cloud import firestore
from google.oauth2 import service_account
from dotenv import load_dotenv
import os


load_dotenv()

GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Tạo Firestore client
def get_db():
    credentials = GOOGLE_APPLICATION_CREDENTIALS
    db = firestore.Client(credentials=credentials)
    return db

db = get_db()
