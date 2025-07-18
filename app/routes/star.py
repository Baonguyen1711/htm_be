from fastapi import APIRouter
from app.models.buzz import BuzzRequest
from ..helper.exception import handle_exceptions
import logging
import traceback

from ..services.realtime_service import set_star

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StarRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api/star")

        self.router.post("/")(self.set_player_star)

    @handle_exceptions
    async def set_player_star( room_id: str, request: BuzzRequest):
        try:
            set_star(room_id, request.player_name)
        except Exception as e:
            return {"error": str(e)}
