from fastapi import APIRouter, HTTPException, File, UploadFile, Body
from fastapi import FastAPI, Depends, UploadFile
from starlette.requests import Request
from firebase_admin import auth
from ..services.auth_service import verify_token
from google.cloud import firestore
from collections import defaultdict
from ..models.questions import UpdateQuestionRequest, Grid
from ..models.users import User
from fastapi.encoders import jsonable_encoder
import shutil
from openpyxl import load_workbook
from io import BytesIO
import logging
import traceback
from app.services.firestore_service import create_room, get_rooms_by_user_id, deactivate_room
from app.services.realtime_service import set_next_round, spectator_join, set_player_answer, send_currrent_turn_to_player
from app.stores.player_store import add_player_info, get_player_info
from firebase_admin import db
import time
from typing import List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

room_routers = APIRouter()




@room_routers.post("/api/room/join")
async def join_room(room_id: str, request: Request, user_info: User):
    user = request.state.user  
    authenticated_uid = user.get("uid")  
    logger.info(f"user: {user_info}")
    logger.info(f"room_id: {room_id}")
    # logger.info(f"user",{request.state.user})
    user_data = user_info.dict()  # Chuyển Pydantic model thành dictionary
    user_data["uid"] = authenticated_uid  # Thêm UID từ token xác thực
    user_data["lastActive"] = int(time.time() * 1000)  # Thêm thời gian
    logger.info(f"user_data: {user_data}")
    if not authenticated_uid:
        logger.info(f"abc")
        raise HTTPException(status_code=401, detail="Unauthorized: User ID not found")
    try:
        logger.info(f"abc")
        try:
            logger.info("Attempting to create reference to Firebase")
            ref = db.reference(f"rooms/{room_id}/players")
            logger.info("Reference created successfully")
            

            # Tiếp tục logic của bạn
        
        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  # Ném lại lỗi để xử lý ở tầng trên nếu cần
        logger.info(f"ref: {ref}")
        players = ref.get() or {}
        logger.info(f"abcde")

        if len(players) >= 4: 
            logger.info(f"abcdef")
            raise HTTPException(status_code=400, detail="Room full")
        try:
            ref.child(authenticated_uid).set(user_data)
            logger.info("Reference created successfully")
            

            # Tiếp tục logic của bạn
        
        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  # Ném lại lỗi để xử lý ở tầng trên nếu cần
        
        logger.info(f"abcdef")
        # Get updated players list after adding the new player
        updated_players = ref.get() or {}
        logger.info(f"abcdeg")

        try:
            for uid, player_data in updated_players.items():
                stt = player_data["stt"]
                player_info_object = {
                        "uid": uid,
                        "userName": player_data["userName"],
                        "avatar": player_data["avatar"],
                        "stt": player_data["stt"],
                        "lastActive": player_data["lastActive"],
                }

                player_info_object_for_answer = {
                    **player_info_object,
                    "answer": "",
                    "row": "",
                    "time": 0,
                    "score": 0,
                    "isObstacle": False,
                    "round_scores": {
                        "1": 0,
                        "2": 0,
                        "3": 0,
                        "4": 0
                    },
                    "was_deducted_this_round": False,
                    "is_correct": False
                }

                add_player_info(room_id, player_info_object)

                set_player_answer(room_id, uid, player_info_object_for_answer)


            logger.info(f"abcdeh")

            # Tiếp tục logic của bạn
        
        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  # Ném lại lỗi để xử lý ở tầng trên nếu cần
        
        
        players_info = get_player_info(room_id)
        return {
            "message": f"User {authenticated_uid} joined room {room_id}",
            "userId": {authenticated_uid},
            "players": players_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating room: {str(e)}")
    

@room_routers.post("/api/room/turn")
def create_new_room(turn: int, room_id: str, request: Request): 

    user = request.state.user
    authenticated_uid = user["uid"]

    if not authenticated_uid:
        raise HTTPException(status_code=401, detail="Unauthorized: User ID not found")

    try:
        send_currrent_turn_to_player(turn,room_id)

        return {"message": "set current turn sucessfully", "stt": turn}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating room: {str(e)}")
    
@room_routers.post("/api/room/create")
def create_new_room(expired_time: int, request: Request): 

    user = request.state.user
    authenticated_uid = user["uid"]

    if not authenticated_uid:
        raise HTTPException(status_code=401, detail="Unauthorized: User ID not found")

    try:
        # Call create_room to generate a unique room ID and save it to Firestore
        result = create_room(authenticated_uid, expired_time)

        return {"message": "Room created successfully", "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating room: {str(e)}")
    

# API Endpoint: Deactivate a room
@room_routers.post("/api/rooms/{room_id}/deactivate")
async def deactivate_room_api(room_id: str, request: Request):
    try:
        user = request.state.user  
        authenticated_uid = user.get("uid")  
        if not authenticated_uid:
            raise HTTPException(status_code=401, detail="Unauthorized: User ID not found")
        result = deactivate_room(authenticated_uid, room_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deactivating room: {str(e)}")
    
# API Endpoint: Fetch rooms by user ID
@room_routers.post("/api/rooms/round")
async def go_to_next_round(room_id: str, round: str,grid: Grid):
    try:
        # user = request.state.user
        # authenticated_uid = user["uid"] 
        # if not authenticated_uid:
        #     raise HTTPException(status_code=401, detail="Unauthorized: User ID not found")
        # try:
            
        #     logger.info("grid", grid)
            

        #     # Tiếp tục logic của bạn
        
        # except Exception as e:
        #     logger.error(f"Error creating Firebase reference: {str(e)}")
        #     logger.error(f"Full traceback: {traceback.format_exc()}")
        #     raise  # Ném lại lỗi để xử lý ở tầng trên nếu cần

        try:
            set_next_round(room_id, round, grid.grid)
            logger.info("set_next_round successfully")
            

            # Tiếp tục logic của bạn
        
        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  # Ném lại lỗi để xử lý ở tầng trên nếu cần
        
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting room: {str(e)}")
    
# API Endpoint: Fetch rooms by user ID
@room_routers.get("/api/rooms")
async def get_rooms(request: Request):
    try:
        user = request.state.user
        authenticated_uid = user["uid"] 
        if not authenticated_uid:
            raise HTTPException(status_code=401, detail="Unauthorized: User ID not found")
        
        result = get_rooms_by_user_id(authenticated_uid)
        # if "error" in result:
        #     raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting room: {str(e)}")
    
@room_routers.post("/api/room/spectator/join")
def spectator_join_room(room_id: str): 
    try:
        spectator_path = spectator_join(room_id)

        return { "spectator_path": spectator_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating room: {str(e)}")
    


