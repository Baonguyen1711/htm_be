from fastapi import APIRouter, HTTPException, File, UploadFile, Body
from starlette.requests import Request
from ..models.questions import UpdateQuestionRequest, Grid
from ..models.users import User
import logging
import traceback
from app.services.realtime_service import set_next_round, spectator_join, set_player_answer, send_currrent_turn_to_player, show_rules, hide_rules
from ..services.room_service import RoomService
from ..helper.exception import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

room_routers = APIRouter()

class RoomRouter:
    def __init__(self,room_service: RoomService):
        self.room_service = room_service
        self.router = APIRouter(prefix="/api/room")

        self.router.get("")(self.get_rooms_by_user_id)

        self.router.post("/validate")(self.validate_room)
        self.router.post("/join")(self.join_room)
        self.router.post("/create")(self.create_new_room)
        self.router.post("/spectator/join")(self.spectator_join_room)


    @handle_exceptions
    async def validate_room(self, room_id: str, password: str = None):
        self.room_service.validate_room(room_id, password)
        return {"message": "Room validation successful"}

    @handle_exceptions
    async def join_room(self, room_id: str, request: Request, user_info: User, password: str = None):
        user = request.state.user
        authenticated_uid = user["uid"]
        updated_players = await self.room_service.join_room(room_id, authenticated_uid, user_info, password)

        return {
            "message": f"User {authenticated_uid} joined room {room_id}",
            "userId": {authenticated_uid},
            "players": updated_players
        }
        
    @handle_exceptions
    def create_new_room(self, expired_time: int, request: Request, password: str = None, max_players: int = 4):
        user = request.state.user
        authenticated_uid = user["uid"]
        room_id = self.room_service.create_room(authenticated_uid, expired_time, password, max_players)
        return {"roomId": room_id, "isActive": True,"message": "Room created successfully!"}

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
    async def get_rooms_by_user_id(self, request: Request):
        user = request.state.user
        authenticated_uid = user["uid"]         
        result = self.room_service.get_rooms_by_user_id(authenticated_uid)
        logger.info(result)
        return result

        
    @handle_exceptions
    def spectator_join_room(self, room_id: str): 
        spectator_path = self.room_service.spectator_join_room(room_id)
        return { "spectator_path": spectator_path}


    