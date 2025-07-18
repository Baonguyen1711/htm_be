from fastapi import APIRouter
from ..models.buzz import BuzzRequest
from ..services.gameService.game_signal_service import GameSignalService
import logging
from ..helper.exception import handle_exceptions
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

buzz_routers = APIRouter()

class BuzzRouter:
    def __init__(self, game_signal_service: GameSignalService):
        self.game_signal_service = game_signal_service
        self.router = APIRouter(prefix="/api/buzz")

        self.router.post("/")(self.buzz_first)
        self.router.post("/open")(self.buzz_open)
        self.router.post("/close")(self.buzz_close)
        self.router.post("/reset")(self.reset_buzz)

    @handle_exceptions
    def reset_buzz(self,room_id:str):
        self.game_signal_service.reset_buzz(room_id)
        return {"status": "reset", "message": "Buzz has been reset"}   

    @handle_exceptions
    def buzz_open(self, room_id:str):
        self.game_signal_service.open_buzz(room_id)
        
    @handle_exceptions
    def buzz_close(self, room_id:str):
        self.game_signal_service.close_buzz(room_id)

    @handle_exceptions
    def buzz_first(self, room_id:str,request: BuzzRequest):
        logger.info(f"playerName {request.player_name}")
        self.game_signal_service.buzz_first(room_id, request.player_name)
        