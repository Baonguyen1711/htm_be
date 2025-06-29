from ..database import db
import datetime
from google.cloud import firestore
import random
from datetime import datetime, timedelta
from ..models.history import History
import logging
import traceback
import bcrypt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_history(user_id: str, data: History):
    logger.info(f"received data {data}")
    db.collection("histories").document(user_id).set(data.dict())

def get_history_by_user_id(user_id: str):
    try:
        doc_ref = db.collection("histories").document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

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
            # "createdAt": firestore.SERVER_TIMESTAMP
        }
        batch.set(question_ref, question_data)
        uploaded_questions += 1

        # Commit batch khi đủ 500 hoặc hết danh sách
        if uploaded_questions % batch_size == 0 or uploaded_questions == len(questions):
            batch.commit()
            print(f"Đã upload {uploaded_questions}/{len(questions)} câu hỏi")
            batch = db.batch()  # Reset batch

    # Tính thời gian thực hiện


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
            # "createdAt": firestore.SERVER_TIMESTAMP
        }
        batch.set(question_ref, question_data)
        uploaded_questions += 1

        # Commit batch khi đủ 500 hoặc hết danh sách
        if uploaded_questions % batch_size == 0 or uploaded_questions == len(questions):
            batch.commit()
            print(f"Đã upload {uploaded_questions}/{len(questions)} câu hỏi")
            batch = db.batch()  # Reset batch

    # Tính thời gian thực hiện


    return {
        "message": f"Upload thành công bộ đề {test_id}",
        "test_id": test_id,
        "total_questions": len(questions),
    }

def upload_single_question_to_firestore(question):
    """
    Upload one question to Firestore.
    
    Parameters:
        rounds (int or str): The round number.
        question (dict): A dictionary representing the question.
        test_id (str): The test ID this question belongs to.
    
    Returns:
        dict: Information about the uploaded question.
    """
    # Tạo document với ID ngẫu nhiên cho câu hỏi
    question_ref = db.collection("questions").document()
    question_id = question_ref.id

    # Dữ liệu câu hỏi
    question_data = {
        "stt": question.get("stt"),
        "questionId": question_id,
        "testId": question["testId"],
        "round": question["answer"],
        "question": question["question"],
        "answer": question["answer"],
        "imgUrl": question.get("imgUrl"),
        "type": question.get("type"),
        "difficulty": question.get("difficulty"),
        "packetName": question.get("packetName"),
        # "createdAt": firestore.SERVER_TIMESTAMP
    }

    # Upload câu hỏi
    question_ref.set(question_data)

    return {
        "message": f"Upload thành công câu hỏi {question_id}",
        "question_id": question_id,
        "test_id": question["testId"]
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

# Password utility functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_room_by_id(room_id: str):
    """Get room data by room ID"""
    try:
        room_ref = db.collection("rooms").document(room_id)
        room_doc = room_ref.get()
        if room_doc.exists:
            return room_doc.to_dict()
        return None
    except Exception as e:
        logging.error(f"Error getting room {room_id}: {e}")
        return None

def validate_room_password(room_id: str, password: str = None) -> bool:
    """Validate room password if room has password protection"""
    try:
        room_data = get_room_by_id(room_id)
        if not room_data:
            return False

        # If room has no password hash, it's not password protected
        if "passwordHash" not in room_data:
            return True

        # If room has password hash but no password provided, validation fails
        if not password:
            return False

        # Verify the password
        return verify_password(password, room_data["passwordHash"])
    except Exception as e:
        logging.error(f"Error validating room password: {e}")
        return False

def create_room(owner_id, duration_in_hours, password: str = None, max_players: int = 4):
    try:
        # Validate max_players
        if max_players < 1 or max_players > 8:
            return {"error": "Max players must be between 1 and 8"}

        room_id = None
        while True:
            room_id = str(random.randint(100000, 999999))
            room_ref = db.collection("rooms").document(room_id)
            doc_snapshot = room_ref.get()
            logging.info(f"doc_snapshot: {doc_snapshot}")
            if not doc_snapshot.exists:
                break  # Room ID is unique

       # Expiration time
        expires_at = datetime.utcnow() + timedelta(hours=duration_in_hours)

        # Prepare room data
        room_data = {
            "ownerId": owner_id,
            # "createdAt": firestore.SERVER_TIMESTAMP,
            "expiresAt": expires_at,
            "isActive": True,
            "maxPlayers": max_players
        }

        # Add password hash if password is provided
        if password:
            room_data["passwordHash"] = hash_password(password)

        # Create room document in Firestore
        db.collection("rooms").document(room_id).set(room_data)

        return {"roomId": room_id, "isActive": True,"message": "Room created successfully!"}
    except Exception as e:
        return {"error": f"An error occurred: {e}"}


def get_rooms_by_user_id(owner_id):
    try:
        # Query the rooms collection for documents with the given owner_id
        rooms_ref = db.collection("rooms").where("ownerId", "==", owner_id)
        rooms_docs = rooms_ref.stream()  # Use stream() to handle multiple documents
        
        # Initialize the result list
        rooms = []
        
        # Iterate through the documents and extract room id and isActive
        for doc in rooms_docs:
            room_data = doc.to_dict()
            rooms.append({
                "roomId": doc.id,          # Document ID (Room ID)
                "isActive": room_data.get("isActive", False)  # Fetch isActive, defaulting to False if missing
            })

        # Check if no rooms were found
        # if not rooms:
        #     return {"error": "No rooms found for this user."}

        return {"rooms": rooms}

    except Exception as e:
        # Handle exceptions and return an error message
        return {"error": f"An error occurred: {str(e)}"}
    
def is_logged_in_user(user_id):
    try:
        # Query the rooms collection for documents with the given owner_id
        logger.info(f"user_id {user_id}")
        users_ref = db.collection("users").document(user_id)
        users = users_ref.get()        
        logger.info(f"users.id {users.id}")

        return users.exists

    except Exception as e:
        # Handle exceptions and return an error message
        return {"error": f"An error occurred: {str(e)}"}
    
def deactivate_room(owner_id: str, room_id: str):
    try:
        # Reference the specific room document by ID
        room_ref = db.collection("rooms").document(room_id)
        room_doc = room_ref.get()  # Fetch the document

        # Check if the room exists
        if not room_doc.exists:
            logging.error(f"Room with ID {room_id} not found.")
            return {"error": f"Room with ID {room_id} not found."}

        # Check if the room is owned by the specified owner
        room_data = room_doc.to_dict()  # Convert document to a dictionary
        if room_data.get("ownerId") != owner_id:
            logging.error(f"Unauthorized: Owner ID {owner_id} does not match.")
            return {"error": "Unauthorized: You do not have permission to deactivate this room."}

        # Deactivate the room by setting "isActive" to False
        room_ref.update({"isActive": False})
        logging.info(f"Room {room_id} deactivated successfully.")
        return {"message": f"Room {room_id} deactivated successfully."}

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return {"error": f"An error occurred: {e}"}
    

def join_room(room_id, user):
    try:
        # Query the rooms collection for documents with the given owner_id
        rooms_ref = db.collection("rooms").where("roomId", "==", room_id)
        rooms_docs = rooms_ref.stream()  # Use stream() to handle multiple documents
        
        # Initialize the result list
        rooms = []
        
        # Iterate through the documents and extract room id and isActive
        for doc in rooms_docs:
            room_data = doc.to_dict()
            room_data.userList.append({
                user
            })

        # Check if no rooms were found
        if not rooms:
            return {"error": "No rooms found for this user."}

        return {"rooms": rooms}

    except Exception as e:
        # Handle exceptions and return an error message
        return {"error": f"An error occurred: {str(e)}"}
    
def save_file_key_for_user(user_id: str, file_key: str, description: str = None):
    
    files_collection = db.collection("users").document(user_id).collection("uploadedFiles")
    file_doc = files_collection.document()  # auto-generated ID

    file_data = {
        "key": file_key,
        "uploadedAt": firestore.SERVER_TIMESTAMP,
    }
    if description:
        file_data["description"] = description

    file_doc.set(file_data)


