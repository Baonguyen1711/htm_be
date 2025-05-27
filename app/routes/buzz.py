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
from ..models.buzz import BuzzRequest
from fastapi.encoders import jsonable_encoder
from openpyxl import load_workbook
from io import BytesIO
from typing import Optional, List
import logging
import traceback
from app.services.firestore_service import upload_test_to_firestore, get_test_by_name, get_test_name_by_user_id, update_question
from ..services.test_service import process_test_data, get_specific_question, get_questions_by_round
from ..services.realtime_service import send_question_to_player, send_answer_to_player, start_time, broadcast_player_answer, send_score, buzz_first, reset_buzz, open_buzz, close_buzz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

buzz_routers = APIRouter()

@buzz_routers.post("/api/buzz/reset")
def buzz_in(room_id:str):
    try:
        reset_buzz(room_id)
        return {"status": "reset", "message": "Buzz has been reset"}   
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@buzz_routers.post("/api/buzz/open")
def buzz_open(room_id:str,request: BuzzRequest):
    try:
        
        try:
            logger.info("Attempting to create reference to Firebase")
            open_buzz(room_id)
            
            

            # Tiếp tục logic của bạn
        
        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  # Ném lại lỗi để xử lý ở tầng trên nếu cần
        # result = buzz_first(room_id, request.stt, request.player_name)
        logger.info(f"abc")
        # if result:
        #     return {"status": "success", "message": "You buzzed in first!"}
        # else:
        #     raise HTTPException(status_code=409, detail="Someone already buzzed in.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@buzz_routers.post("/api/buzz/close")
def buzz_close(room_id:str,request: BuzzRequest):
    try:
        
        try:
            logger.info("Attempting to create reference to Firebase")
            
            close_buzz(room_id)
            

            # Tiếp tục logic của bạn
        
        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  # Ném lại lỗi để xử lý ở tầng trên nếu cần

        logger.info(f"abc")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@buzz_routers.post("/api/buzz")
def buzz_in(room_id:str,request: BuzzRequest):
    try:
        logger.info(f"playerName {request.player_name}")
        try:
            logger.info("Attempting to create reference to Firebase")
            result = buzz_first(room_id, request.stt, request.player_name)
            logger.info(f"buzz successfully {result}")
            

            # Tiếp tục logic của bạn
        
        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  # Ném lại lỗi để xử lý ở tầng trên nếu cần
        # result = buzz_first(room_id, request.stt, request.player_name)
        logger.info(f"abc")
        # if result:
        #     return {"status": "success", "message": "You buzzed in first!"}
        # else:
        #     raise HTTPException(status_code=409, detail="Someone already buzzed in.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))