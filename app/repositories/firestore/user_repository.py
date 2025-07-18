from fastapi import logger
from .base import BaseRepository
import logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__("users")

    def is_logged_in_user(self, user_id):
        logger.info(f"user_id {user_id}")
        users = self.get_document(user_id)

        return users

    
    