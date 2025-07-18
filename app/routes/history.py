from fastapi import APIRouter
from starlette.requests import Request
from ..models.history import History
from ..services.history_service import HistoryService
from ..helper.exception import handle_exceptions
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HistoryRouter:
    def __init__(self, history_service: HistoryService):
        self.history_service = history_service
        self.router = APIRouter(prefix="/api/history")

        self.router.post("/update")(self.update_match_history)

        self.router.get("/retrive")(self.get_history_by_user)

    @handle_exceptions
    def update_match_history(self, data: History, request: Request):
        user = request.state.user
        authenticated_uid = user["uid"]
        self.history_service.update_match_history(data, authenticated_uid)

    @handle_exceptions
    def get_history_by_user(self, request: Request):
        user = request.state.user
        authenticated_uid = user["uid"]

        logger.info("Attempting to create reference to Firebase")
        history = self.history_service.get_history_by_user_id(authenticated_uid)
        logger.info(f"history {history}")

        return history

        