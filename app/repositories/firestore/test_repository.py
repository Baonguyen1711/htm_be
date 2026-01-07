import json
import re
from .base import BaseRepository
from ...util.gemini import prompting
from ...constants.gemini_prompt import EXTRACT_IDEA_PROMPT
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import random

class TestRepository(BaseRepository):
    def __init__(self, database):
        super().__init__("tests", database)
    
    def get_test_by_id(self, test_id):
        return self.get_document(test_id)
    
    def get_total_question_by_test_id(self, test_id):
        logger.info(f"test_id in repo: {test_id}")
        test_data = self.get_test_by_id(test_id)
        logger.info(f"test_data in repo: {test_data}")
        return test_data.get("totalQuestions")
    
    def get_test_name_by_test_id(self, test_id):
        test_data = self.get_test_by_id(test_id)
        return test_data.get("testName")
    
    def get_owner_by_test_id(self, test_id):
        test_data = self.get_test_by_id(test_id)
        return test_data.get("owner")
    
    def extract_idea_and_link(self, questions_and_answers):
        
        questions_json = json.dumps(questions_and_answers, ensure_ascii=False)
        prompt_filled = EXTRACT_IDEA_PROMPT.replace("{questions}", questions_json)
        print("prompt filled", prompt_filled)

        data = prompting(prompt_filled)

        # Loại bỏ ```json ``` nếu có
        # cleaned_text = re.sub(r"^```(json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
        print("data", data)
    
        # try:
        #     data = json.loads(raw_text)
        #     print("data",data)
        # except json.JSONDecodeError as e:
        #     print("JSON parse error:", e)
        #     print("Raw text from Gemini:", repr(raw_text))
        #     raise e

        return data
    
    def set_test_by_batch(self, questions, test_id, round):
        batch = self.database.batch()
        batch_size = 500  
        uploaded_questions = 0
        local_questions_and_answers = []

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
                "answer_value": q.get("answer_value") if q.get("answer_value") else q["answer"],
                "answerA": q.get("answerA") if q.get("answerA") else None,
                "answerB": q.get("answerB") if q.get("answerB") else None,
                "answerC": q.get("answerC") if q.get("answerC") else None,
                "answerD": q.get("answerD") if q.get("answerD") else None,
                "imgUrl": q.get("imgUrl"),
                "type": q.get("type"),
                "difficulty": q.get("difficulty"),
                "packetName": q.get("packetName"),
                "catergory": q.get("catergory"),
                "randomKey": q.get("randomKey")
                # "createdAt": firestore.SERVER_TIMESTAMP
            }
            batch.set(question_ref, question_data)
            uploaded_questions += 1

            local_questions_and_answers.append({
                "questionId": question_id,
                "question": q["question"],
                "answer": q["answer"],
            })

            # Commit batch khi đủ 500 hoặc hết danh sách
            if uploaded_questions % batch_size == 0 or uploaded_questions == len(questions):
                batch.commit()
                print(f"Đã upload {uploaded_questions}/{len(questions)} câu hỏi")
                batch = self.database.batch()  # Reset batch

        self.update_test(test_id, {"totalQuestions": len(questions)})

        print("local_questions_and_answers",local_questions_and_answers)
        ideas_and_link = []
        try:
            ideas_and_link = self.extract_idea_and_link(local_questions_and_answers)
        except Exception as e:
            print("Error khi extract idea:", e)
            ideas_and_link = []

        update_batch = self.database.batch()
        for item in ideas_and_link:
            question_ref = self.database.collection("questions").document(item["questionId"])
            update_batch.update(question_ref, {
                "keyIdea": item.get("keyIdea"),
                "referenceLink": item.get("referenceLink")
            })

        update_batch.commit()
        print(f"Đã thêm idea và link cho {len(ideas_and_link)} câu hỏi")


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
        doc_id = self.create_new_document(data)

        self.update_document(doc_id, {
            "testId": doc_id
        })

        return doc_id
    
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
    