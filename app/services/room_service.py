import datetime
import random
import time
from typing import List
import bcrypt
from fastapi import HTTPException, logger

from ..models.users import User
from ..repositories.firestore.room_repository import RoomRepository
from ..repositories.realtimedb.game_repository import GameRepository
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RoomService:
    def __init__(self, room_repository:RoomRepository, game_repository: GameRepository):
        self.room_repository = room_repository
        self.game_repository = game_repository

    def get_room_by_id(self, room_id):
        return self.room_repository.get_room_by_id(room_id)
    
    def get_rooms_by_user_id(self, user_id):
        return self.room_repository.get_rooms_by_user_id(user_id)
    
    def create_room(self, data):
        return self.room_repository.create_room(data)
    
    def update_room(self, room_id, data):
        self.room_repository.update_room(room_id, data)

    def validate_room(self, room_id,password: str = None):
        room_data = self.get_room_by_id(room_id)
        if not room_data:
            raise HTTPException(status_code=404, detail="Room not found")

        if not self.validate_room_password(room_id, password):
            raise HTTPException(status_code=403, detail="Invalid room password")

        return {"message": "Room validation successful"}
    
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def validate_room_password(self, room_id: str, password: str = None) -> bool:
        try:
            room_data = self.room_repository.get_room_by_id(room_id)
            if not room_data:
                return False

            # If room has no password hash, it's not password protected
            if "passwordHash" not in room_data:
                return True

            # If room has password hash but no password provided, validation fails
            if not password:
                return False

            # Verify the password
            return self.verify_password(password, room_data["passwordHash"])
        except Exception as e:
            logger.error(f"Error validating room password: {e}")
            return False

    def create_room(self, owner_id, duration_in_hours, password: str = None, max_players: int = 4):
        # Validate max_players
        if max_players < 4 or max_players > 8:
            return {"error": "Max players must be between 4 and 8"}

        room_id = None
        while True:
            room_id = str(random.randint(100000, 999999))
            existed_room_id = self.get_room_by_id(room_id)
            logger.info(f"doc_snapshot: {existed_room_id}")
            if not existed_room_id:
                break  

        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=duration_in_hours)
        room_data = {
            "ownerId": owner_id,
            # "createdAt": firestore.SERVER_TIMESTAMP,
            "expiresAt": expires_at,
            "isActive": True,
            "maxPlayers": max_players
        }

        # Add password hash if password is provided
        if password:
            room_data["passwordHash"] = self.hash_password(password)

        self.room_repository.create_room(room_data, room_id)

        return room_id
   
    
    async def join_room(self, room_id: str, uid: str, user_info: User, password: str = None):
        logger.info(f"user: {user_info}")
        logger.info(f"room_id: {room_id}")
        # logger.info(f"user",{request.state.user})
        player_info = user_info.dict()  # Chuyển Pydantic model thành dictionary
        player_info["uid"] = uid  # Thêm UID từ token xác thực
        player_info["lastActive"] = int(time.time() * 1000)  
        logger.info(f"player_info: {player_info}")

        # Validate room password and get room data
        room_data = self.get_room_by_id(room_id)
        if not room_data:
            raise HTTPException(status_code=404, detail="Room not found")

        if not self.validate_room_password(room_id, password):
            raise HTTPException(status_code=403, detail="Invalid room password")

        # Get max players from room data (default to 4 for backward compatibility)
        max_players = room_data.get("maxPlayers", 4)
        players = self.game_repository.get_players_in_room(room_id) or []

        if len(players) >= max_players:
            logger.info(f"room full")
            raise HTTPException(status_code=400, detail="Room full")

        self.game_repository.set_player_to_room(room_id, uid, player_info)
        logger.info("Reference created successfully")
    
        # Get updated players list after adding the new player
        updated_players = self.game_repository.get_players_in_room(room_id)

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

            self.game_repository.set_single_player_answer(room_id, uid, player_info_object_for_answer)
            
        # players_info = get_player_info(room_id)
        return list(updated_players)
    
    def spectator_join_room(self, room_id: str): 
        spectator_path = self.game_repository.set_spectator_to_room(room_id)

        return spectator_path

        