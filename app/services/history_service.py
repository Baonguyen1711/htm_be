from fastapi import logger

from ..models.history import History
from ..repositories.firestore.history_repository import HistoryRepository 
import logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HistoryService:
    def __init__(self, history_repository: HistoryRepository):
        self.history_repository = history_repository

    def update_match_history(self, data: History, uid: str):
        logger.info("Attempting to create reference to Firebase")
        self.history_repository.update_history(uid, data)
        logger.info(f"updated_data {data}")

    def get_history_by_user_id(self, uid: str):
        logger.info("Attempting to create reference to Firebase")
        history = self.history_repository.get_history_by_user_id(uid)
        logger.info(f"history {history}")
        return history