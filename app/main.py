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
    allow_origins=["http://localhost:3000", "https://28a2-2402-9d80-a50-f638-115b-68ac-7642-3852.ngrok-free.app"],  # Specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Specify allowed methods
    allow_headers=["*"],  # Specify allowed headers
    expose_headers=["Set-Cookie"]
)


@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI with Firestore and Realtime DB"}


@app.middleware("http")
async def dispatch(request: Request, call_next):
    # Skip middleware for preflight OPTIONS requests
    if request.method == "OPTIONS":
        return await call_next(request)
    if request.url.path in ["/api/auth/token", "/api/room/validate", "/api/auth/verify","/api/room/spectator/join", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)

    
    token = request.cookies.get("authToken")
    logger.info(f"Token: {token}")  
    
    if not token:
        return Response(content='{"error": "Unauthorized"}', status_code=401, media_type="application/json")

    try:
        # Try to verify as Firebase ID token first
        try:
            decoded_token = auth.verify_id_token(token)
        except Exception as firebase_error:
            # If Firebase verification fails, try our custom JWT
            logger.info(f"Firebase verification failed: {firebase_error}, trying custom JWT")
            import jwt
            SECRET_KEY = os.getenv("JWT_SECRET_KEY")
            logger.info(f"JWT Secret Key exists: {bool(SECRET_KEY)}")
            if SECRET_KEY:
                try:
                    # Decode JWT without audience verification (since we control the token)
                    decoded_token = jwt.decode(
                        token,
                        SECRET_KEY,
                        algorithms=["HS256"],
                        options={"verify_aud": False}  # Skip audience verification
                    )
                    logger.info(f"JWT decoded successfully: {decoded_token}")
                    # Validate it's our API verification token
                    if decoded_token.get("token_type") != "api_verification":
                        raise Exception("Invalid token type")
                    # Ensure required fields exist
                    if not decoded_token.get("uid"):
                        raise Exception("Missing uid in token")
                    logger.info("Custom JWT verification successful")
                except jwt.ExpiredSignatureError:
                    logger.error("JWT token expired")
                    return Response(content='{"error": "Token expired"}', status_code=401, media_type="application/json")
                except jwt.InvalidTokenError as jwt_error:
                    logger.error(f"JWT decode error: {jwt_error}")
                    raise Exception(f"Invalid JWT token: {jwt_error}")
                except Exception as custom_error:
                    logger.error(f"Custom JWT validation error: {custom_error}")
                    raise Exception(f"Custom JWT validation failed: {custom_error}")
            else:
                raise Exception("No JWT secret key configured")

        request.state.user = decoded_token
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return Response(content='{"error": "Invalid token"}', status_code=401, media_type="application/json")

    return await call_next(request)













