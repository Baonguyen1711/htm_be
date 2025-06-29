from fastapi import FastAPI
from app.routes.tests import test_routers
from app.routes.rooms import room_routers
from app.routes.auth import auth_routers
from app.routes.buzz import buzz_routers
from app.routes.star import star_routers
from app.routes.history import history_routers
from app.services.s3_service import S3Service
from app.services.sound_service import SoundService
from app.routes.s3 import S3Router
from app.routes.sound import SoundRouter
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


s3_service = S3Service()  
sound_service = SoundService()

sound_router = SoundRouter(sound_service)
s3_router = S3Router(s3_service)

app.include_router(s3_router.router)
app.include_router(sound_router.router)
# Đăng ký router từ module routes
app.include_router(test_routers)
app.include_router(room_routers)
app.include_router(auth_routers)
app.include_router(buzz_routers)
app.include_router(star_routers)
app.include_router(history_routers)

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
    if request.url.path in ["/api/auth/token","/api/auth/verify","/api/room/spectator/join", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)

    
    token = request.cookies.get("authToken")
    logger.info(f"Token: {token}")  
    
    if not token:
        return Response(content='{"error": "Unauthorized"}', status_code=401, media_type="application/json")

    try:
        decoded_token = auth.verify_id_token(token)  
        request.state.user = decoded_token  
    except Exception as e:
        return Response(content='{"error": "Invalid token"}', status_code=401, media_type="application/json")

    return await call_next(request)













