import traceback
from firebase_admin import db
from typing import Any, Dict, List, Optional
import logging
import datetime
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from ..models.questions import Answer, PlacementArray
from ..models.scores import Score, ScoreRule
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

def update_score_each_round(room_id:str,data: any, round: str):
    logger.info(f"data {data}")
    ref = db.reference(f"rooms/{room_id}/round_scores/{round}")
    ref.set(data)

def send_packet_name_to_player(packet_list:List[str], room_id:str):

    ref = db.reference(f"/rooms/{room_id}/packets")
    ref.set(packet_list)

def send_selected_packet_name_to_player(packet:str, room_id:str):

    ref = db.reference(f"/rooms/{room_id}/selectedPacket")
    ref.set(packet)

def send_currrent_turn_to_player(stt:int, room_id:str):

    ref = db.reference(f"/rooms/{room_id}/turn")
    ref.set(stt)

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

def is_existing_player(room_id:str, uid:str):
    logger.info(f"uid {uid}")
    ref = db.reference(f"/rooms/{room_id}/player_answer/{uid}")
    data = ref.get()
    if data is not None:
        return True
    else: 
        return False

def send_score(room_id:str,mode:str, score:Optional[List[Score]] = None):
    try:        
        logger.info(f"roomid {room_id}")
        logger.info(f"List[Score] {score}")
        logger.info(f"mode {mode}")
        ref = db.reference(f"/rooms/{room_id}/scores")
        ref.set(score)


    except Exception as e:
        logger.error(f"Error creating Firebase reference: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise

def set_next_round(room_id:str, round: str, grid: Optional[List[List[str]]] = None):
    logger.info(f"current round {round}")
    ref = db.reference(f"/rooms/{room_id}/rounds")
    ref.set({
        "round": round,
        "grid": grid
    })

def send_obstacle(room_id:str, obstacle: str, placementArray: List[PlacementArray]):
    logger.info(f"answer {room_id}")
    logger.info(f"obstacle {obstacle}")
    ref = db.reference(f"/rooms/{room_id}/obstacles")
    ref.set({
        "obstacle": obstacle,
        "placementArray": placementArray
    })

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

def set_star(room_id: str, player_name: str):
    star_ref = db.reference(f"rooms/{room_id}/star")
    star_ref.set(player_name)


def reset_star(room_id: str):
    star_ref = db.reference(f"rooms/{room_id}/star")
    star_ref.delete()

def play_sound(room_id: str, type: str):
    logger.info(f"sound {type}")
    ref = db.reference(f"/rooms/{room_id}/sound")
    ref.set(type)

def send_score_rule(room_id: str, rules: ScoreRule):
    logger.info(f"rules {rules}")
    ref = db.reference(f"/rooms/{room_id}/rules")
    ref.set(rules)

def spectator_join(room_id):
    ref = db.reference(f"/rooms/{room_id}/spectators").push()
    ref.set(True)
    return ref.path

def set_single_player_answer(room_id: str, uid: str, player_data: Dict[str, Any]) -> None:
    try:
        ref = db.reference(f"rooms/{room_id}/player_answer/{uid}")
        ref.set(player_data)
        # def transaction_update(current_data: Dict[str, Any] | None) -> Dict[str, Any]:
        #     if current_data is None:
        #         # New player
        #         return player_data
        #     else:
        #         # Existing player, update relevant fields, preserve score and round_scores
        #         current_data.update({
        #             "answer": player_data["answer"],
        #             "stt": player_data["stt"],
        #             "row": player_data["row"],
        #             "time": player_data["time"],
        #             "isObstacle": player_data["isObstacle"],
        #             "is_correct": player_data["is_correct"],
        #             "player_name": player_data["player_name"],
        #             "avatar": player_data["avatar"]
        #         })
        #         return current_data
        # ref.transaction(transaction_update)
        logger.info(f"Successfully updated answer for uid {uid} in room {room_id}")
    except Exception as e:
        logger.error(f"Error setting answer for uid {uid} in room {room_id}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise


def set_player_answer(room_id: str, uid: str,player_data: Dict[str, Any]) -> None:
    try:
        ref = db.reference(f"rooms/{room_id}/player_answer/{uid}")
        ref.set(player_data)
    except Exception as e:
        logger.error(f"Error setting player_answer in transaction for room {room_id}: {str(e)}")
        raise

def get_all_player_answer(room_id: str) -> List[Dict[str, Any]]:

    try:
        ref = db.reference(f"rooms/{room_id}/player_answer")
        data = ref.get()
        if data is None:
            logger.info(f"No player_answer data found for room {room_id}")
            return []
        # Convert dictionary to list
        logger.info(f"data {data}")
        players = list(data.values()) 
        logger.info(f"Retrieved player_answer for room {room_id} {players}")
        return players
    except Exception as e:
        logger.error(f"Error getting player_answer for room {room_id}: {str(e)}")
        raise


def get_player_answer(room_id: str, uid: str) -> Dict[str, Any]:

    try:
        ref = db.reference(f"rooms/{room_id}/player_answer/{uid}")
        data = ref.get()
        if data is None:
            logger.info(f"No player_answer data found for room {room_id}")
            return None

        players = data
        logger.info(f"Retrieved player_answer for room {room_id} {players}")
        return players
    except Exception as e:
        logger.error(f"Error getting player_answer for room {room_id}: {str(e)}")
        raise

def set_player_answer_correct(room_id: str, correct_data: List[Dict[str, Any]]) -> None:

    try:
        ref = db.reference(f"rooms/{room_id}/player_answer_correct")
        data = {player["stt"]: player for player in correct_data}
        ref.set(data)
        logger.info(f"Set player_answer_correct for room {room_id}")
    except Exception as e:
        logger.error(f"Error setting player_answer_correct for room {room_id}: {str(e)}")
        raise

def get_player_answer_correct(room_id: str) -> List[Dict[str, Any]]:

    try:
        ref = db.reference(f"rooms/{room_id}/player_answer_correct")
        data = ref.get()
        if data is None:
            logger.info(f"No player_answer_correct data found for room {room_id}")
            return []
        players = list(data.values())
        logger.info(f"Retrieved player_answer_correct for room {room_id}")
        return players
    except Exception as e:
        logger.error(f"Error getting player_answer_correct for room {room_id}: {str(e)}")
        raise

def set_player_info(room_id: str, player_info: List[Dict[str, Any]]) -> None:

    try:
        ref = db.reference(f"rooms/{room_id}/player_info")
        data = {player["stt"]: player for player in player_info}
        ref.set(data)
        logger.info(f"Set player_info for room {room_id}")
    except Exception as e:
        logger.error(f"Error setting player_info for room {room_id}: {str(e)}")
        raise

def get_player_info(room_id: str) -> List[Dict[str, Any]]:

    try:
        ref = db.reference(f"rooms/{room_id}/player_info")
        data = ref.get()
        if data is None:
            logger.info(f"No player_info data found for room {room_id}")
            return []
        players = list(data.values())
        logger.info(f"Retrieved player_info for room {room_id}")
        return players
    except Exception as e:
        logger.error(f"Error getting player_info for room {room_id}: {str(e)}")
        raise

def set_score_rules(room_id: str, rules: Dict[str, Any]) -> None:

    try:
        ref = db.reference(f"rooms/{room_id}/rules")
        ref.set(rules)
        logger.info(f"Set score_rules for room {room_id}")
    except Exception as e:
        logger.error(f"Error setting score_rules for room {room_id}: {str(e)}")
        raise

def get_score_rules(room_id: str) -> Dict[str, Any]:

    try:
        ref = db.reference(f"rooms/{room_id}/rules")
        data = ref.get()
        if data is None:
            logger.info(f"No score_rules found for room {room_id}, returning default")
            return {
                "round1": [15, 10, 10, 10],
                "round2": [15, 10, 10, 10],
                "round3": 10,
                "round4": [10, 20, 30]
            }
        logger.info(f"Retrieved score_rules for room {room_id}")
        return data
    except Exception as e:
        logger.error(f"Error getting score_rules for room {room_id}: {str(e)}")
        raise

def set_current_correct_answer(room_id: str, answer: str) -> None:

    try:
        ref = db.reference(f"rooms/{room_id}/current_correct_answer")
        ref.set(answer)
        logger.info(f"Set current_correct_answer for room {room_id}")
    except Exception as e:
        logger.error(f"Error setting current_correct_answer for room {room_id}: {str(e)}")
        raise

def get_current_correct_answer(room_id: str) -> str:

    try:
        ref = db.reference(f"rooms/{room_id}/current_correct_answer")
        data = ref.get()
        if data is None:
            logger.info(f"No current_correct_answer found for room {room_id}")
            return ""
        logger.info(f"Retrieved current_correct_answer for room {room_id}")
        return data
    except Exception as e:
        logger.error(f"Error getting current_correct_answer for room {room_id}: {str(e)}")
        raise

def update_score_each_round(room_id: str, data: Dict[str, Any], round: str) -> None:

    try:
        logger.info(f"Setting round scores data for room {room_id}, round {round}: {data}")
        ref = db.reference(f"rooms/{room_id}/round_scores/{round}")
        ref.set(data)
        logger.info(f"Set round scores for room {room_id}, round {round}")
    except Exception as e:
        logger.error(f"Error setting round scores for room {room_id}, round {round}: {str(e)}")
        raise

def get_score_each_round(room_id: str, round: str) -> Dict[str, Any]:

    try:
        ref = db.reference(f"rooms/{room_id}/round_scores/{round}")
        data = ref.get()
        if data is None:
            logger.info(f"No round scores found for room {room_id}, round {round}")
            return {}
        logger.info(f"Retrieved round scores for room {room_id}, round {round}")
        return data
    except Exception as e:
        logger.error(f"Error getting round scores for room {room_id}, round {round}: {str(e)}")
        raise