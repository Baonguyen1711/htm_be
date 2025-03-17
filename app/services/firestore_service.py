from ..database import db
import datetime
from google.cloud import firestore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_user_to_firestore(user_id: str, data: dict):
    db.collection("users").document(user_id).set(data)

def get_user_from_firestore(user_id: str):
    user_doc = db.collection("users").document(user_id).get()
    if user_doc.exists:
        return user_doc.to_dict()
    return None

def get_test_by_test_id(test_id):
    try:
        questions_ref = db.collection("questions").where("testId", "==", test_id)
        docs = questions_ref.stream()

        questions = []
        for doc in docs:
            question_data = doc.to_dict()
            question_data['id'] = doc.id
            questions.append(question_data)

        return {"questions": questions}
    except Exception as e:
        return {"error": f"An error occurred: {e}"}
    


def upload_test_to_firestore(rounds, questions, test_id):

    # Bắt đầu đo thời gian
    start_time = datetime.datetime.now()


    # 2. Upload câu hỏi vào collection "questions" với ID ngẫu nhiên
    batch = db.batch()
    batch_size = 500  # Giới hạn 500 operations mỗi batch
    uploaded_questions = 0

    for i, q in enumerate(questions, start=1):
        # Tạo document với ID ngẫu nhiên cho câu hỏi
        question_ref = db.collection("questions").document()  # ID ngẫu nhiên
        question_id = question_ref.id

        # Dữ liệu câu hỏi
        question_data = {
            "stt": q.get("stt"),
            "questionId": question_id,
            "testId": test_id,
            "round": rounds,
            "question": q["question"],
            "answer": q["answer"],
            "imgUrl": q.get("imgUrl"),
            "type": q.get("type"),
            "difficulty": q.get("difficulty"),
            "packetName": q.get("packetName"),
            "createdAt": firestore.SERVER_TIMESTAMP
        }
        batch.set(question_ref, question_data)
        uploaded_questions += 1

        # Commit batch khi đủ 500 hoặc hết danh sách
        if uploaded_questions % batch_size == 0 or uploaded_questions == len(questions):
            batch.commit()
            print(f"Đã upload {uploaded_questions}/{len(questions)} câu hỏi")
            batch = db.batch()  # Reset batch

    # Tính thời gian thực hiện
    duration = (datetime.datetime.now() - start_time).total_seconds()

    return {
        "message": f"Upload thành công bộ đề {test_id}",
        "test_id": test_id,
        "total_questions": len(questions),
    }

def get_test_by_name(test_owner, test_name):
    test_ref = (db.collection("tests")
                .where("testName","==", test_name)
                .where("owner","==", test_owner))
    tests = test_ref.get()

    logging.info(f"tests: {tests}")

    result = []

    for test in tests:
        test_data = test.to_dict()
        logging.info(f"test_data: {type (test_data)}")
        test_id = test_data["testId"]

        logging.info(f"test_id: {type (test_id)}")
        #get from questions
        question_ref = db.collection("questions").where("testId", "==", test_id)
        questions = question_ref.get()

        if questions:
            # Convert QuerySnapshot to list of dictionaries
            question_list = [q.to_dict() for q in questions] if questions else []

            # Combine test and its questions into a plain dict
            result.append({
                "test": test_data,
                "questions": question_list
            })

    
    return result

def get_test_by_test_id(test_id):
    try:
        questions_ref = db.collection("questions").where("testId", "==", test_id)
        docs = questions_ref.stream()

        questions = []
        for doc in docs:
            question_data = doc.to_dict()
            question_data['id'] = doc.id
            questions.append(question_data)

        return {"questions": questions}
    except Exception as e:
        return {"error": f"An error occurred: {e}"}
    


def upload_test_to_firestore(rounds, questions, test_id):

    # Bắt đầu đo thời gian
    start_time = datetime.datetime.now()


    # 2. Upload câu hỏi vào collection "questions" với ID ngẫu nhiên
    batch = db.batch()
    batch_size = 500  # Giới hạn 500 operations mỗi batch
    uploaded_questions = 0

    for i, q in enumerate(questions, start=1):
        # Tạo document với ID ngẫu nhiên cho câu hỏi
        question_ref = db.collection("questions").document()  # ID ngẫu nhiên
        question_id = question_ref.id

        # Dữ liệu câu hỏi
        question_data = {
            "stt": q.get("stt"),
            "questionId": question_id,
            "testId": test_id,
            "round": rounds,
            "question": q["question"],
            "answer": q["answer"],
            "imgUrl": q.get("imgUrl"),
            "type": q.get("type"),
            "difficulty": q.get("difficulty"),
            "packetName": q.get("packetName"),
            "createdAt": firestore.SERVER_TIMESTAMP
        }
        batch.set(question_ref, question_data)
        uploaded_questions += 1

        # Commit batch khi đủ 500 hoặc hết danh sách
        if uploaded_questions % batch_size == 0 or uploaded_questions == len(questions):
            batch.commit()
            print(f"Đã upload {uploaded_questions}/{len(questions)} câu hỏi")
            batch = db.batch()  # Reset batch

    # Tính thời gian thực hiện
    duration = (datetime.datetime.now() - start_time).total_seconds()

    return {
        "message": f"Upload thành công bộ đề {test_id}",
        "test_id": test_id,
        "total_questions": len(questions),
    }

def get_test_name_by_user_id(user_id):
    try:
        test_ref = (db.collection("tests")
                    .where("owner","==", user_id))
        tests = test_ref.get()

        logging.info(f"tests: {tests}")

        result = []

        if tests:
            for test in tests:
                test_data = test.to_dict()
                logging.info(f"test_data: {type (test_data)}")
                test_name = test_data["testName"] 
                result.append(test_name)  

                logging.info(f"test_id: {type (result)}")
        else:
            return None
        return result
    except Exception as e:
        return {"error": f"An error occurred: {e}"}
    
def update_question(question_id: str, updated_data: dict):
    try:
        # Reference to the question document (assuming questions are in a 'questions' collection)
        question_ref = db.collection("questions").document(question_id)

        # Fetch the existing document to verify it exists
        question_doc = question_ref.get()

        if not question_doc.exists:
            logging.error(f"Question with ID {question_id} not found.")
            return {"error": f"Question with ID {question_id} not found."}

        # Update the document with the provided data
        question_ref.update(updated_data)

        return {"message": f"Question {question_id} updated successfully."}

    except Exception as e:
        logging.error(f"Unexpected error updating question {question_id}: {e}")
        return {"error": f"An unexpected error occurred: {e}"}

    


