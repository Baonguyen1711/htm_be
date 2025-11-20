from typing import Optional
from .base import BaseRepository
import random 
from secrets import SystemRandom
import logging 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class QuestionRepository(BaseRepository):
    def __init__(self, database):
        super().__init__("questions", database)
    
    def get_question_by_id(self, question_id):
        return self.get_document(question_id)
    
    def get_questions_by_test_id(self, test_id):
        filters = [("testId", "==", test_id)]
        return self.get_documents_by_filter(filters)

    def get_random_question_from_database(self, limit: int, catergory: Optional[str] = None):
        rand = SystemRandom()  # cryptographically secure generator
        random_key = rand.random()
        logger.info(f"selected random key {random_key}")

        filters = [("randomKey", ">=", random_key)]
        if catergory:
            filters.append(("catergory", "==", catergory))

        docs = self.get_documents_by_filter(filters=filters, limit=limit)

        logger.info(f"random question from db {docs}")
        # If not enough results, query from the other side
        if len(docs) < limit:
            extended_filters = [("randomKey", "<", random_key)]
            extended_docs = self.get_documents_by_filter(filters=extended_filters, limit=limit)
            logger.info(f"extended random question from db {docs}")
            docs.extend([doc for doc in extended_docs])

        return docs
    
    def get_test_id_by_question_id(self, question_id):
        question_data = self.get_question_by_id(question_id)
        return question_data.get("testId")
    
    def create_question(self, data):
        return self.create_new_document(data)
    
    def update_question(self, question_id, data):
        self.update_document(question_id, data)
    
    def delete_question(self, question_id):
        self.delete_document(question_id)

    def public_question(self, question_id):
        self.update_document(question_id, {"isPublic": True})

    def private_question(self, question_id):
        self.update_document(question_id, {"isPublic": False})
