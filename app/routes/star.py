from fastapi import APIRouter
from app.models.buzz import BuzzRequest
import logging
import traceback

from ..services.realtime_service import set_star

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

star_routers = APIRouter()

@star_routers.post("/api/star")
async def set_player_star( room_id: str, request: BuzzRequest):
    try:
        set_star(room_id, request.player_name)
    except Exception as e:
        return {"error": str(e)}
