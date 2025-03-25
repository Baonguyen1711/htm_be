from firebase_admin import db
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cấu hình Realtime Database
def send_realtime_notification(data: dict):
    ref = db.reference("/notifications")
    ref.push(data)

def send_question_to_player(question: dict, room_id:str):
    logger.info(f"question {question}")
    ref = db.reference(f"/rooms/{room_id}/questions")
    ref.set( question)

def send_answer_to_player(answer: str, room_id:str):
    logger.info(f"answer {answer}")
    ref = db.reference(f"/rooms/{room_id}/answers")
    ref.set(answer)

def start_time(room_id:str):
    logger.info(f"answer {room_id}")
    ref = db.reference(f"/rooms/{room_id}/times")
    ref.set("START")
