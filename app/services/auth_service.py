from fastapi import HTTPException, Request, logger
from fastapi.responses import JSONResponse
from firebase_admin import auth
from ..repositories.firestore.room_repository import RoomRepository 
from ..repositories.firestore.user_repository import UserRepository
import jwt
import time
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ACCESS_TOKEN_EXPIRE_SECONDS = 30 * 60  # 30 minutes 
REFRESH_TOKEN_EXPIRE_SECONDS = 4* 60 * 60  # 7 days

class AuthService:
    def __init__(self, room_repository: RoomRepository, user_repository: UserRepository):
        self.room_repository = room_repository
        self.user_repository = user_repository

    def verify_token(self, token: str):
        try:
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(token)
            return decoded_token  # Return the decoded token, which includes the user's uid and email.
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        

    def create_room_token(self, room_id: str, role: str, user_id: str = None):
        SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        payload = {
            "roomId": room_id,
            "role": role,
            "userId": user_id or "anon_" + str(int(time.time() * 1000)),
            "exp": time.time() + 30*60  
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token
    

    async def generate_tokens(self, request):
        SECRET_KEY = os.getenv("JWT_SECRET_KEY")

        data = await request.json()
        room_id = data.get("roomId")
        role = ""   
        user = request.state.user
        user_id = user["uid"]
        logger.info(f"userId {user_id}")
        allowed_room_id = self.room_repository.get_rooms_by_user_id(user_id)
        logger.info(f"allowed_room_id {allowed_room_id}")
        # rooms = []

        # for room_data in allowed_room_id:
        #     rooms.append({
        #         "roomId": room_data.get("id"),         
        #         "isActive": room_data.get("isActive", False)  
        #     })

        logger.info(f"allowed_room_id {allowed_room_id}")
        is_host_user = self.user_repository.is_logged_in_user(user_id)
        logger.info(f"is_host_user {is_host_user}")

        exists = any(room["roomId"] == room_id for room in allowed_room_id)

        if not room_id:
            raise HTTPException(400, "Missing roomId")

        if exists:
            role = "host"
        elif not is_host_user:
            role = "player"
        else:
            raise HTTPException(status_code=403, detail="You do not have access to this room")

        access_payload = {
            "roomId": room_id,
            "role": role,
            "userId": user_id,
            "exp": time.time() + ACCESS_TOKEN_EXPIRE_SECONDS
        }
        access_token = jwt.encode(access_payload, SECRET_KEY, algorithm="HS256")


        refresh_payload = {
            "userId": user_id,
            "roomId": room_id,
            "role": role,
            "exp": time.time() + REFRESH_TOKEN_EXPIRE_SECONDS
        }
        refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm="HS256")
        

        return access_token, refresh_token





    async def verify_room_token(self, request: Request):
        SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        auth_header = request.headers.get("Authorization")
        logger.info(f"auth_header {auth_header}")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")
        
        token = auth_header[len("Bearer "):]
        logger.info(f"token {token}")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    

    async def refresh_access_token(self, request: Request):
        SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        refresh_token = request.cookies.get("refreshToken")

        if not refresh_token:
            raise HTTPException(status_code=401, detail="Missing refresh token")

        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("userId")
            room_id = payload.get("roomId")
            role = payload.get("role")

            access_payload = {
                "userId": user_id,
                "roomId": room_id,
                "role": role,
                "exp": time.time() + ACCESS_TOKEN_EXPIRE_SECONDS
            }

            access_token = jwt.encode(access_payload, SECRET_KEY, algorithm="HS256")

            return access_token

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    async def verify_is_host(self, uid):
        is_host_user = self.user_repository.is_logged_in_user(uid)

        return is_host_user
        

    async def authenticate(self, request: Request):
        data = await request.json()
        id_token = data.get("token")

        try:

            decoded_token = auth.verify_id_token(id_token)

            uid = decoded_token.get("uid")
            email = decoded_token.get("email")


            SECRET_KEY = os.getenv("JWT_SECRET_KEY")
            logger.info(f"Creating JWT with secret key exists: {bool(SECRET_KEY)}")

            api_token_payload = {
                "uid": uid,
                "email": email,
                "email_verified": decoded_token.get("email_verified", False),
                "auth_time": decoded_token.get("auth_time"),
                "iss": "htm-custom-auth",  # Our custom issuer
                "aud": decoded_token.get("aud"),
                "exp": int(time.time()) + (60*60*5), 
                "iat": int(time.time()),
                "sub": uid,
                "token_type": "api_verification"  # Mark this as our custom token
            }

            logger.info(f"JWT payload: {api_token_payload}")

            api_token = jwt.encode(api_token_payload, SECRET_KEY, algorithm="HS256")
            logger.info(f"JWT token created successfully, length: {len(api_token)}")

            # Ensure token is string (newer PyJWT versions return string, older return bytes)
            if isinstance(api_token, bytes):
                api_token = api_token.decode('utf-8')

            return api_token, decoded_token
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {"error": str(e)}
