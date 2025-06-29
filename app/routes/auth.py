import time
from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi import FastAPI, Depends, UploadFile
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import Response
from firebase_admin import auth
from ..database import db
from ..services.auth_service import verify_token
from google.cloud import firestore
from collections import defaultdict
from ..models.questions import UpdateQuestionRequest, Answer
from ..models.scores import Score
from fastapi.encoders import jsonable_encoder
from openpyxl import load_workbook
from io import BytesIO
from typing import Optional, List
import logging
import traceback
from app.services.firestore_service import get_rooms_by_user_id, is_logged_in_user
from ..services.test_service import process_test_data, get_specific_question, get_questions_by_round
from ..services.realtime_service import send_question_to_player, send_answer_to_player, start_time, broadcast_player_answer, send_score
import jwt
import os
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_routers = APIRouter()

ACCESS_TOKEN_EXPIRE_SECONDS = 30 * 60  # 30 minutes 
REFRESH_TOKEN_EXPIRE_SECONDS = 4* 60 * 60  # 7 days

@auth_routers.post("/api/auth/access_token")
async def generate_tokens(request: Request):
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    data = await request.json()
    room_id = data.get("roomId")
    role = ""   
    user = request.state.user
    user_id = user["uid"]
    logger.info(f"userId {user_id}")
    allowed_room_id = get_rooms_by_user_id(user_id)
    logger.info(f"allowed_room_id {allowed_room_id}")
    is_host_user = is_logged_in_user(user_id)
    logger.info(f"is_host_user {is_host_user}")

    exists = any(room["roomId"] == room_id for room in allowed_room_id["rooms"])

    if not room_id:
        raise HTTPException(400, "Missing roomId")

    if exists:
        role = "host"
    elif not is_host_user:
        role = "player"
    else:
        raise HTTPException(status_code=403, detail="You do not have access to this room")

    try:
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

        response = JSONResponse({
            "accessToken": access_token,
        })

        response.set_cookie(
            key="refreshToken",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=REFRESH_TOKEN_EXPIRE_SECONDS
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token generation failed: {str(e)}")

@auth_routers.post("/api/auth/verify")
async def verify_room_token(request: Request):
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
    
@auth_routers.post("/api/auth/refresh")
async def refresh_access_token(request: Request):
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

        return JSONResponse({
            "accessToken": access_token
        })

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
@auth_routers.post("/api/auth/isHost")
async def verify_is_host(request: Request, response: Response):
    user = request.state.user
    authenticated_uid = user["uid"]

    try:
        is_host_user = is_logged_in_user(authenticated_uid)

        return is_host_user
    except Exception as e:
        return {"error": str(e)}


@auth_routers.post("/api/auth/token")
async def authenticate(request: Request, response: Response):
    data = await request.json()
    id_token = data.get("token")

    try:
        decoded_token = auth.verify_id_token(id_token)
        response.set_cookie(
            key="authToken",
            value=id_token,
            httponly=True,  
            secure=True,
            samesite="Strict",
            max_age=3600  
        )
        return {"message": "Authenticated", "user": decoded_token}
    except Exception as e:
        return {"error": str(e)}
