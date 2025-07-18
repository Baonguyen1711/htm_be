from .base import BaseRepository

class QuestionRepository(BaseRepository):
    def __init__(self):
        super().__init__("questions")
    
    def get_question_by_id(self, question_id):
        return self.get_document(question_id)
    
    def get_questions_by_test_id(self, test_id):
        filters = [("testId", "==", test_id)]
        return self.get_documents_by_filter(filters)
    
    def create_question(self, data):
        return self.create_new_document(data)
    
    def update_question(self, question_id, data):
        self.update_document(question_id, data)
    
    def delete_question(self, question_id):
        self.delete_document(question_id)
    
