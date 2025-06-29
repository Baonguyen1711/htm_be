from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi import FastAPI, Depends, UploadFile
from starlette.requests import Request
from firebase_admin import auth
from ..database import db
from ..services.auth_service import verify_token
from google.cloud import firestore
from collections import defaultdict
from ..models.questions import UpdateQuestionRequest, Answer, Grid, PlacementArray
from ..models.scores import Score, ScoreRule
from ..models.history import History
from fastapi.encoders import jsonable_encoder
from openpyxl import load_workbook
from io import BytesIO
from typing import Optional, List
import logging
import traceback
from app.stores.player_store import get_player_info
from app.services.firestore_service import upload_test_to_firestore, get_test_by_name, get_test_name_by_user_id, update_question, upload_single_question_to_firestore, update_history, get_history_by_user_id
from ..services.test_service import process_test_data, get_specific_question, get_questions_by_round, get_packet_name
from ..services.realtime_service import send_question_to_player, send_answer_to_player, start_time, broadcast_player_answer, send_score, send_round_2_grid_to_player, send_selected_row_to_player, send_incorrect_row_to_player, send_correct_row_to_player, send_obstacle, send_packet_name_to_player, send_current_question_to_player, send_selected_cell_to_player, send_cell_color_to_player, send_score_rule
import re


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

history_routers = APIRouter()


@history_routers.post("/api/history/update")
def update_match_history(data: History, request: Request):
    try:
        user = request.state.user
        authenticated_uid = user["uid"]

        logger.info("Attempting to create reference to Firebase")
        update_history(authenticated_uid, data)
        logger.info(f"updated_data {data}")

        
    
    except Exception as e:
        logger.error(f"Error creating Firebase reference: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise 

@history_routers.get("/api/history/retrive")
def get_history_by_user(request: Request):
    try:
        user = request.state.user
        authenticated_uid = user["uid"]

        logger.info("Attempting to create reference to Firebase")
        history = get_history_by_user_id(authenticated_uid)
        logger.info(f"history {history}")

        
    
    except Exception as e:
        logger.error(f"Error creating Firebase reference: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise 

    return history

    