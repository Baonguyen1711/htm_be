from typing import Dict
from fastapi import APIRouter
from starlette.requests import Request
from ..models.questions import  Grid
from ..models.users import User
import logging
import traceback
from ..services.room_service import RoomService
from ..helper.exception import handle_exceptions
from ..helper.host_only import host_only
from ..dependencies.router_dependencies import get_room_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

room_routers = APIRouter()

class RoomRouter:
    def __init__(self, room_service: RoomService = None):
        # FIXED: Accept actual service instance, not Depends() object
        self.room_service = room_service or get_room_service()
        self.router = APIRouter(prefix="/api/room")

        self.router.get("/user")(self.get_rooms_by_user_id)

        self.router.post("/validate")(self.validate_room)
        self.router.get("/info")(self.get_room_info)
        self.router.post("/join")(self.join_room)
        self.router.post("/create")(self.create_new_room)
        self.router.post("/spectator/join")(self.spectator_join_room)
        self.router.post("/kick")(self.kick_player)

        self.router.post("/update")(self.update_room)


    @handle_exceptions
    async def validate_room(self, room_id: str, password: str = None):
        self.room_service.validate_room(room_id, password)
        return {"message": "Room validation successful"}

    @handle_exceptions
    async def get_room_info(self, room_id: str, password: str = None, request: Request = None):
        # This endpoint doesn't require authentication, just room validation
        room_info = await self.room_service.get_room_info(room_id, password)
        return room_info

    @handle_exceptions
    async def join_room(self, room_id: str, request: Request, user_info: User, password: str = None):
        user = request.state.user
        authenticated_uid = user["uid"]
        updated_players = await self.room_service.join_room(room_id, authenticated_uid, user_info, password)
        logger.info(f"updated_players {updated_players}")
        logger.info(f"list updated_players {list( updated_players)}")

        return {
            "message": f"User {authenticated_uid} joined room {room_id}",
            "uid": {authenticated_uid},
            "players":  updated_players
        }
        
    @handle_exceptions
    def create_new_room(self, request: Request, expired_time: int, room_mode: str, password: str = None, max_players: int = 4):
        user = request.state.user
        authenticated_uid = user["uid"]
        
        room_id = self.room_service.create_room(authenticated_uid, room_mode, expired_time, password, max_players)
        return {"roomId": room_id, "isActive": True,"message": "Room created successfully!"}

    @handle_exceptions
    def create_practice_room(self, request: Request, room_id: str, room_data: Dict[str, str]):
        user = request.state.user
        authenticated_uid = user["uid"]

        self.room_service.create_practice_room(room_id, room_data)
        logger.info(f"Practice room {room_id} created by {authenticated_uid}")

        
        return {"message": "Practice room created successfully", "roomId": room_id}
    
    @handle_exceptions
    def update_room(self, request: Request, room_id: str, test_name: str):
        user = request.state.user
        authenticated_uid = user["uid"]

        self.room_service.add_test_name_to_room(room_id, test_name)
        return {"message": "Add test name to room successfully", "test_name": test_name}

    # API Endpoint: Deactivate a room
    # @room_routers.post("/api/rooms/{room_id}/deactivate")
    # async def deactivate_room_api(room_id: str, request: Request):
    #     try:
    #         user = request.state.user  
    #         authenticated_uid = user.get("uid")  
    #         if not authenticated_uid:
    #             raise HTTPException(status_code=401, detail="Unauthorized: User ID not found")
    #         result = deactivate_room(authenticated_uid, room_id)
    #         if "error" in result:
    #             raise HTTPException(status_code=404, detail=result["error"])
    #         return result
    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail=f"Error deactivating room: {str(e)}")        

    @handle_exceptions
    @host_only
    async def get_rooms_by_user_id(self, request: Request):
        user = request.state.user
        authenticated_uid = user["uid"]         
        result = self.room_service.get_rooms_by_user_id(authenticated_uid)
        logger.info(result)
        return result

        
    @handle_exceptions
    def spectator_join_room(self, room_id: str):
        spectator_path = self.room_service.spectator_join_room(room_id)
        logger.info(f"spectator_path {spectator_path}")
        return { "spectator_path": spectator_path}

    @handle_exceptions
    @host_only
    async def kick_player(self, room_id: str, player_uid: str, request: Request):
        user = request.state.user
        authenticated_uid = user["uid"]

        # Verify that the requester is the host/owner of the room
        room_data = self.room_service.get_room_by_id(room_id)
        if not room_data:
            raise ValueError("Room not found")

        if room_data.get("ownerId") != authenticated_uid:
            raise ValueError("Only the room owner can kick players")

        # Remove player from room
        result = await self.room_service.kick_player(room_id, player_uid)
        logger.info(f"Player {player_uid} kicked from room {room_id} by {authenticated_uid}")

        return {
            "message": f"Player {player_uid} has been kicked from room {room_id}",
            "kicked_player": player_uid,
            "updated_players": result
        }


    