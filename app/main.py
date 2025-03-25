from fastapi import FastAPI
from app.routes.tests import test_routers
from app.routes.rooms import room_routers
from fastapi.middleware.cors import CORSMiddleware
# from .middleware.auth import AuthMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, status, Depends
import firebase_admin
from firebase_admin import auth, credentials
from .database import db
import time
import traceback
from dotenv import load_dotenv
import os




import logging

logger = logging.getLogger(__name__)

load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

app = FastAPI()

cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)  # Replace with your Firebase service account key file path
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://htm-be-default-rtdb.asia-southeast1.firebasedatabase.app/'  # For Realtime Database
})



# Đăng ký router từ module routes
app.include_router(test_routers)
app.include_router(room_routers)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Specify allowed methods
    allow_headers=["*"],  # Specify allowed headers
)


@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI with Firestore and Realtime DB"}


@app.middleware("http")
async def dispatch(request: Request, call_next):
    # Skip middleware for preflight OPTIONS requests
    if request.method == "OPTIONS":
        return await call_next(request)
    # Skip middleware for public routes
    if request.url.path in ["/docs"]:
        return await call_next(request)
    # Extract the Authorization header
    auth_header = request.headers.get("authorization")
    # logger.info(f"auth_header: {auth_header}")
    if not auth_header or not auth_header.startswith("Bearer"):
        logger.info(f"abc")
        # logger.info(f"auth_header: {auth_header}")
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]

    # logger.info(f"token: {token}")


    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        # logger.info(f"decoded_token: {decoded_token}")
        email = decoded_token.get("email")
        logger.info(f"email: {email}")
        # Check Firestore for the whitelisted email
        # doc_ref = db.collection("allowed_emails").document(email)
        # doc = doc_ref.get()
        # logger.info(f"doc: {doc}")
        # if not doc.exists:
        #     raise HTTPException(status_code=403, detail="Email not authorized")
        
        # Proceed to the next middleware/endpoint
        request.state.user = decoded_token  # You can store user info in the request state
        # logger.info(f"request.state.user: {request.state.user}")
        return await call_next(request)

    except Exception as e:
        logger.error(f"Invalid or expired token: {str(e)}")
        logger.error(f"Full exception traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
# # Add AuthMiddleware after, without any keyword arguments


# Add CORS middleware first












