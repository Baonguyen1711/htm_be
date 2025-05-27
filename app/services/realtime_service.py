from firebase_admin import db
from typing import List, Optional
import logging
import datetime
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from ..models.questions import Answer
from ..models.scores import Score
from ..models.buzz import BuzzRequest
import json
# # Cấu hình Realtime Database
# def send_realtime_notification(data: dict):
#     ref = db.reference("/notifications")
#     ref.push(data)

def send_question_to_player(room_id:str, question: Optional[dict] | None = None,question_chunk:Optional[List[dict]] | None = None,):
    logger.info(f"question {question}")
    ref = db.reference(f"/rooms/{room_id}/questions")
    ref.set( question)

def send_current_question_to_player(room_id:str,question_number:int):
    logger.info(f"question {question_number}")
    ref = db.reference(f"/rooms/{room_id}/currentQuestions")
    ref.set(question_number)

def send_packet_name_to_player(packet_list:List[str], room_id:str):

    ref = db.reference(f"/rooms/{room_id}/packets")
    ref.set(packet_list)

def send_round_2_grid_to_player(grid: List[List[str]], room_id:str):
    logger.info(f"question {grid}")
    ref = db.reference(f"/rooms/{room_id}/grid")
    ref.set( grid)

def send_answer_to_player(answer: str, room_id:str):
    logger.info(f"answer {answer}")
    ref = db.reference(f"/rooms/{room_id}/answers")
    ref.set(answer)

def start_time(room_id:str):
    logger.info(f"room_id {room_id}")
    ref = db.reference(f"/rooms/{room_id}/times")
    ref.set(int(datetime.datetime.utcnow().timestamp() * 1000))

def send_selected_cell_to_player(room_id: str, row_index: str, col_index:str):
    logger.info(f"answer {room_id}")
    ref = db.reference(f"/rooms/{room_id}/cell")
    ref.set({
        "rowIndex": row_index,
        "colIndex": col_index
    })

def send_cell_color_to_player(room_id: str, row_index: str, col_index:str, color: str):
    logger.info(f"answer {room_id}")
    ref = db.reference(f"/rooms/{room_id}/color")
    ref.set({
        "rowIndex": row_index,
        "colIndex": col_index,
        "color": color
    })

def send_selected_row_to_player(room_id: str, selected_row_number: str, is_row: bool,word_length: int):
    logger.info(f"answer {room_id}")
    ref = db.reference(f"/rooms/{room_id}/select")
    ref.set({
        "selected_row_number":selected_row_number,
        "is_row": is_row,
        "word_length": word_length
    })

def send_incorrect_row_to_player(room_id: str, selected_row_number: str, is_row:bool, word_length: int):
    logger.info(f"answer {room_id}")
    ref = db.reference(f"/rooms/{room_id}/incorrect")
    ref.set({
        "selected_row_number":selected_row_number,
        "is_row": is_row,
        "word_length": word_length
    })


def send_correct_row_to_player(room_id: str, selected_row_number: str, correct_answer: str, marked_character_index: str, is_row:bool, word_length: int):
    logger.info(f"answer {room_id}")
    logger.info(f"marked_character_index {marked_character_index}")

    ref = db.reference(f"/rooms/{room_id}/correct")
    ref.set({
        "selected_row_number":selected_row_number,
        "correct_answer":correct_answer,
        "marked_character_index":json.loads(marked_character_index),
        "is_row": is_row
    })

def broadcast_player_answer(room_id:str, answer:List[Answer]):
    logger.info(f"answer {answer}")
    ref = db.reference(f"/rooms/{room_id}/answerLists")
    ref.set(answer)

def send_score(room_id:str, score:List[Score]):
    logger.info(f"answer {room_id}")
    logger.info(f"List[Score] {score}")
    ref = db.reference(f"/rooms/{room_id}/scores")
    ref.set(score)

def set_next_round(room_id:str, round: str, grid: Optional[List[List[str]]] = None):
    logger.info(f"current round {round}")
    ref = db.reference(f"/rooms/{room_id}/rounds")
    ref.set({
        "round": round,
        "grid": grid
    })

def send_obstacle(room_id:str, obstacle: str):
    logger.info(f"answer {room_id}")
    logger.info(f"obstacle {obstacle}")
    ref = db.reference(f"/rooms/{room_id}/obstacles")
    ref.set(obstacle)

def buzz_first(room_id:str,stt:str, player_name: str):
    buzz_ref = db.reference(f"rooms/{room_id}/buzzedPlayer")

    def transaction_update(current_value):
        if current_value is None:
            return player_name
        return current_value 
    
    result = buzz_ref.transaction(transaction_update)
    if result == player_name:
        return True
    else:
        return False
    
def reset_buzz(room_id: str):
    buzz_ref = db.reference(f"rooms/{room_id}/buzzedPlayer")
    buzz_ref.delete()

def open_buzz(room_id: str):
    buzz_ref = db.reference(f"rooms/{room_id}/openBuzzed")
    buzz_ref.set("open")


def close_buzz(room_id: str):
    buzz_ref = db.reference(f"rooms/{room_id}/openBuzzed")
    buzz_ref.delete()

def play_sound(room_id: str, type: str):
    logger.info(f"sound {type}")
    ref = db.reference(f"/rooms/{room_id}/sound")
    ref.set(type)
