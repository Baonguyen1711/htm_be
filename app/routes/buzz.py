from fastapi import APIRouter, Request
from ..models.buzz import BuzzRequest
from ..services.gameService.game_signal_service import GameSignalService
import logging
from ..helper.exception import handle_exceptions
from ..helper.host_only import host_only
from ..dependencies.router_dependencies import get_game_signal_service
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

buzz_routers = APIRouter()

class BuzzRouter:
    def __init__(self, game_signal_service: GameSignalService = None):
        # FIXED: Accept actual service instance, not Depends() object
        self.game_signal_service = game_signal_service or get_game_signal_service()
        self.router = APIRouter(prefix="/api/buzz")

        self.router.post("/")(self.buzz_first)
        self.router.post("/open")(self.buzz_open)
        self.router.post("/close")(self.buzz_close)
        self.router.post("/reset")(self.reset_buzz)

    @handle_exceptions
    @host_only
    def reset_buzz(self, request: Request,room_id:str):
        self.game_signal_service.reset_buzz(room_id)
        return {"status": "reset", "message": "Buzz has been reset"}   

    @handle_exceptions
    @host_only
    def buzz_open(self, request: Request,  room_id:str):
        self.game_signal_service.open_buzz(room_id)
        
    @handle_exceptions
    @host_only
    def buzz_close(self, request: Request,  room_id:str):
        self.game_signal_service.close_buzz(room_id)

    @handle_exceptions
    def buzz_first(self, room_id:str,request: BuzzRequest):
        logger.info(f"playerName {request.player_name}")
        self.game_signal_service.buzz_first(room_id, request.player_name)
        