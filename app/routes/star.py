from fastapi import APIRouter
from app.models.buzz import BuzzRequest
from ..helper.exception import handle_exceptions
import logging
import traceback
from ..services.realtime_service import set_star
from ..dependencies.router_dependencies import get_game_signal_service
from ..services.gameService.game_signal_service import GameSignalService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StarRouter:
    def __init__(self, game_signal_service: GameSignalService = None):
        self.game_signal_service = game_signal_service or get_game_signal_service()
        self.router = APIRouter(prefix="/api/star")

        self.router.post("/")(self.set_player_star)
        self.router.post("/reset")(self.reset_buzz)

    @handle_exceptions
    async def set_player_star(self, room_id: str, request: BuzzRequest):
        try:
            set_star(room_id, request.player_name)
        except Exception as e:
            return {"error": str(e)}

    @handle_exceptions
    async def reset_buzz(self,room_id:str):
        self.game_signal_service.reset_star(room_id)
        return {"status": "reset", "message": "Buzz has been reset"} 
