import datetime
import random
import time
from typing import Any, List
import bcrypt
from fastapi import HTTPException, Depends
from sympy import Dict

from ..models.users import User
from ..repositories.firestore.room_repository import RoomRepository
from ..repositories.realtimedb.game_repository import GameRepository
# FIXED: Import from service_dependencies instead of router_dependencies to break circular import
from ..dependencies.service_dependencies import get_room_repository, get_game_repository
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RoomService:
    def __init__(self, room_repository:RoomRepository = Depends(get_room_repository), game_repository: GameRepository = Depends(get_game_repository)):
        self.room_repository = room_repository
        self.game_repository = game_repository

    def get_room_by_id(self, room_id):
        return self.room_repository.get_room_by_id(room_id)
    
    def get_rooms_by_user_id(self, user_id):
        return self.room_repository.get_rooms_by_user_id(user_id)
    
    def create_room(self, data, is_practice=False):
        return self.room_repository.create_room(data, is_practice=is_practice)

    def create_practice_room(self, room_id: str, room_data: Any) -> None:
        self.game_repository.create_practice_room(room_id, room_data)
        self.join_room(room_id, room_data["uid"], User(**room_data))

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

    def create_room(self, owner_id, room_mode, duration_in_hours, password: str = None, max_players: int = 4):
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
            "roomMode": room_mode,
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

    async def get_room_info(self, room_id: str, password: str = None):
        """Get room information including max players and current players with their positions"""
        # Validate room password and get room data
        room_data = self.get_room_by_id(room_id)
        if not room_data:
            raise HTTPException(status_code=404, detail="Room not found")

        if not self.validate_room_password(room_id, password):
            raise HTTPException(status_code=403, detail="Invalid room password")

        # Get current players
        current_players_raw = self.game_repository.get_players_in_room(room_id)
        current_players = []
        if current_players_raw is not None:
            # Filter out None values and ensure we only have valid player objects
            current_players = [player for player in current_players_raw if player is not None and isinstance(player, dict)]

        # Get max players from room data
        max_players = room_data.get("maxPlayers", 4)

        # Get occupied positions
        occupied_positions = [int(player.get("stt", 0)) for player in current_players if player.get("stt")]

        # Generate available positions
        available_positions = [i for i in range(1, max_players + 1) if i not in occupied_positions]

        status = self.game_repository.get_room_status(room_id)

        return {
            "room_id": room_id,
            "max_players": max_players,
            "room_mode": room_data.get("roomMode", "multiplayer"),
            "current_players_count": len(current_players),
            "occupied_positions": occupied_positions,
            "available_positions": available_positions,
            "status": status,
            "current_players": [
                {
                    "uid": player.get("uid"),
                    "userName": player.get("userName"),
                    "stt": player.get("stt"),
                    "avatar": player.get("avatar")
                } for player in current_players
            ]
        }

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
        current_player_list = list(self.game_repository.get_players_in_room(room_id)) if self.game_repository.get_players_in_room(room_id) is not None else []

        if len(current_player_list) >= max_players:
            logger.info(f"room full")
            raise HTTPException(status_code=400, detail="Room full")

        # Check if position (stt) is already taken
        requested_position = player_info.get("stt")
        if requested_position:
            occupied_positions = [player.get("stt") for player in current_player_list if player.get("stt")]
            if requested_position in occupied_positions:
                raise HTTPException(status_code=409, detail=f"Position {requested_position} is already taken")

            # Validate position is within valid range
            try:
                position_int = int(requested_position)
                if position_int < 1 or position_int > max_players:
                    raise HTTPException(status_code=400, detail=f"Position must be between 1 and {max_players}")
            except ValueError:
                raise HTTPException(status_code=400, detail="Position must be a valid number")

        logger.info(f"current_player_list before: {current_player_list}")        
        logger.info(f"player_info: {player_info}")
        current_player_list.append(player_info)
        
        logger.info(f"current_player_list after: {current_player_list}")
        self.game_repository.set_player_to_room(room_id, current_player_list)
        logger.info("Reference created successfully")
    
        # Get updated players list after adding the new player
        updated_players = self.game_repository.get_players_in_room(room_id)
        logger.info(f"updated_players: {updated_players}")

        # for player in updated_players:
        #     player_info_object = {
        #             "uid": player["uid"],
        #             "userName": player["userName"],
        #             "avatar": player["avatar"],
        #             "stt": player["stt"],
        #             "lastActive": player["lastActive"],
        #     }

        player_info_object_for_answer = {
            **player_info,
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

        score_object = {
            **{k: v for k, v in player_info.items() if k != "userName"},
            "playerName": player_info.get("userName"),
            "score": 0,
        }

        current_score_list = list(self.game_repository.get_score_list(room_id)) if self.game_repository.get_score_list(room_id) is not None else []
        logger.info(f"current_score_list before: {current_score_list}")
        # Check if the user's score is already in the list to avoid duplicates
        if not any(score["uid"] == uid for score in current_score_list):
            current_score_list.append(score_object)

        logger.info(f"current_score_list after: {current_score_list}")
        
        self.game_repository.send_score_list(room_id, current_score_list)

        self.game_repository.set_single_player_answer(room_id, uid, player_info_object_for_answer)
            
        # players_info = get_player_info(room_id)
        return updated_players
    
    def spectator_join_room(self, room_id: str):
        spectator_path = self.game_repository.set_spectator_to_room(room_id)

        return spectator_path

    async def kick_player(self, room_id: str, player_uid: str):
        """
        Remove a player from the room
        """
        logger.info(f"Kicking player {player_uid} from room {room_id}")

        # Get current players list
        current_players = self.game_repository.get_players_in_room(room_id)
        if not current_players:
            raise ValueError("No players found in room")

        # Convert to list if it's not already
        players_list = list(current_players) if current_players else []

        # Find and remove the player
        updated_players = [player for player in players_list if player.get("uid") != player_uid]

        if len(updated_players) == len(players_list):
            raise ValueError(f"Player {player_uid} not found in room")

        # Update the players list in Firebase
        self.game_repository.set_player_to_room(room_id, updated_players)

        logger.info(f"Player {player_uid} successfully kicked from room {room_id}")
        logger.info(f"Updated players count: {len(updated_players)}")

        return updated_players

        