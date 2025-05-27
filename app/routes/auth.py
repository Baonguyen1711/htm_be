from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi import FastAPI, Depends, UploadFile
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
from app.services.firestore_service import upload_test_to_firestore, get_test_by_name, get_test_name_by_user_id, update_question
from ..services.test_service import process_test_data, get_specific_question, get_questions_by_round
from ..services.realtime_service import send_question_to_player, send_answer_to_player, start_time, broadcast_player_answer, send_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_routers = APIRouter()

@auth_routers.post("/api/auth")
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
        )
        return {"message": "Authenticated", "user": decoded_token}
    except Exception as e:
        return {"error": str(e)}
