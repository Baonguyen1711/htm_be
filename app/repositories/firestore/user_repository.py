from fastapi import logger
from .base import BaseRepository
import logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRepository(BaseRepository):
    def __init__(self, database):
        super().__init__("users", database)

    def is_logged_in_user(self, user_id):
        logger.info(f"user_id {user_id}")
        users = self.get_document(user_id)

        return users
    
    def create_user(self, email: str, role: str, uid: str):
        user_object = {
            "email": email,
            "role": role,
            "uid": uid   
        }
        self.create_new_document(user_object, uid)

        return user_object
    
    def get_users(self):
        users = self.get_all_documents()
        return users



    
    