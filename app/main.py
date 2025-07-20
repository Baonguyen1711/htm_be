from fastapi import FastAPI, Depends
from app.routes.tests import TestRouter
from app.routes.rooms import RoomRouter
from app.routes.auth import AuthRouter
from app.routes.buzz import BuzzRouter
from app.routes.star import StarRouter
from app.routes.history import HistoryRouter
from app.routes.s3 import S3Router
from app.routes.sound import SoundRouter
from app.routes.game import GameRouter



from fastapi.middleware.cors import CORSMiddleware
# from .middleware.auth import AuthMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import firebase_admin
from firebase_admin import auth, credentials

import os
import logging

logger = logging.getLogger(__name__)
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
DATABASE_URL = os.getenv('DATABASE_URL')
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL
    })


app = FastAPI()

# cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)  # Replace with your Firebase service account key file path
# firebase_admin.initialize_app(cred, {
#     'databaseURL': 'https://htm-be-default-rtdb.asia-southeast1.firebasedatabase.app/'  # For Realtime Database
# })

# app.include_router(S3Router(get_s3_service()).router)
# app.include_router(SoundRouter(get_sound_service()).router)
# app.include_router(TestRouter(get_test_service()).router)
# app.include_router(RoomRouter(get_room_service()).router)
# app.include_router(AuthRouter().router)
# app.include_router(BuzzRouter(get_game_signal_service()).router)
# app.include_router(GameRouter(get_game_data_service(), get_game_signal_service(), get_test_service()).router)
# app.include_router(HistoryRouter(get_history_service()).router)

# test_repository = TestRepository()
# room_repository = RoomRepository()
# question_repository = QuestionRepository()
# user_repository = UserRepository()
# history_repository = HistoryRepository()
# game_repository = GameRepository()
# realtime_question_repository = RealtimeQuestionRepository()

# test_service = TestService(test_repository, question_repository, realtime_question_repository)
# game_data_service = GameDataService(game_repository, test_service)
# game_signal_service = GameSignalService(game_repository, test_service)
# s3_service = S3Service()  
# sound_service = SoundService()
# auth_service = AuthService(room_repository, user_repository)
# history_service = HistoryService(history_repository)
# room_service = RoomService(room_repository, game_repository)

# FIXED: Create services manually and pass to routers (Manual Dependency Injection)
from app.dependencies.router_dependencies import (
    get_s3_service, get_sound_service, get_test_service, get_room_service,
    get_auth_service, get_game_signal_service, get_game_data_service,
    get_history_service
)

# Create routers with manually injected services
sound_router = SoundRouter(get_sound_service())
s3_router = S3Router(get_s3_service())
test_routers = TestRouter(get_test_service())
room_routers = RoomRouter(get_room_service())
auth_routers = AuthRouter(get_auth_service())
buzz_routers = BuzzRouter(get_game_signal_service())
game_routers = GameRouter(get_game_data_service(), get_game_signal_service(), get_test_service())
star_routers = StarRouter()  # This one might not need services
history_routers = HistoryRouter(get_history_service())

app.include_router(s3_router.router)
app.include_router(sound_router.router)
app.include_router(test_routers.router)
app.include_router(room_routers.router)
app.include_router(auth_routers.router)
app.include_router(buzz_routers.router)
app.include_router(star_routers.router)
app.include_router(game_routers.router)
app.include_router(history_routers.router)

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













