from .base import BaseRepository
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRepository(BaseRepository):
    def __init__(self):
        super().__init__("tests")
    
    def get_test_by_id(self, test_id):
        return self.get_document(test_id)
    
    def set_test_by_batch(self, questions, test_id, round):
        batch = self.database.batch()
        batch_size = 500  # Giới hạn 500 operations mỗi batch
        uploaded_questions = 0

        for i, q in enumerate(questions, start=1):
            # Tạo document với ID ngẫu nhiên cho câu hỏi
            question_ref = self.database.collection("questions").document() 
            question_id = question_ref.id

            # Dữ liệu câu hỏi
            question_data = {
                "stt": q.get("stt"),
                "questionId": question_id,
                "testId": test_id,
                "round": round,
                "question": q["question"],
                "answer": q["answer"],
                "imgUrl": q.get("imgUrl"),
                "type": q.get("type"),
                "difficulty": q.get("difficulty"),
                "packetName": q.get("packetName"),
                # "createdAt": firestore.SERVER_TIMESTAMP
            }
            batch.set(question_ref, question_data)
            uploaded_questions += 1

            # Commit batch khi đủ 500 hoặc hết danh sách
            if uploaded_questions % batch_size == 0 or uploaded_questions == len(questions):
                batch.commit()
                print(f"Đã upload {uploaded_questions}/{len(questions)} câu hỏi")
                batch = self.database.batch()  # Reset batch


        return {
            "message": f"Upload thành công bộ đề {test_id}",
            "test_id": test_id,
            "total_questions": len(questions),
        }
    
    def get_test_by_test_name(self, test_name, owner_id):
        filters = [("testName", "==", test_name), ("owner", "==", owner_id)]
        return self.get_documents_by_filter(filters)
    
    def get_tests_by_user_id(self, user_id):
        filters = [("owner", "==", user_id)]
        return self.get_documents_by_filter(filters)
    
    def create_test(self, data):
        return self.create_new_document(data)
    
    def update_test(self, test_id, data):
        self.update_document(test_id, data)
    
    def delete_test(self, test_id):
        self.delete_document(test_id)
    
    def get_test_by_name(self, test_name):
        filters = [("testName", "==", test_name)]
        return self.get_documents_by_filter(filters)
    
    def get_test_by_name_and_user_id(self, test_name, user_id):
        logger.info(f"test_name {test_name}")
        logger.info(f"user_id {user_id}")
        filters = [("testName", "==", test_name), ("owner", "==", user_id)]
        return self.get_documents_by_filter(filters)
    