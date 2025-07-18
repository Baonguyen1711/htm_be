import datetime
import json
from typing import Any, Dict, List, Optional
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ...models.questions import Answer, PlacementArray
from ...models.scores import Score, ScoreRule
from .base import RealTimeBaseRepository

class GameRepository(RealTimeBaseRepository):
    def __init__(self):
        super().__init__()
    
    def set_score_rules(self, room_id: str, rules: ScoreRule) -> None:
        self.set_to_path(f"{room_id}/rules", rules.dict())
    
    def get_score_rules(self, room_id: str) -> Dict[str, Any]:
        return self.read_from_path(f"{room_id}/rules")
    
    def set_player_info(self, room_id: str, player_info: Dict[str, Any]) -> None:
        self.set_to_path(f"{room_id}/player_info", player_info)
    
    def get_player_info(self, room_id: str) -> Dict[str, Any]:
        return self.read_from_path(f"{room_id}/player_info")
    
    def set_score_each_round(self, room_id: str, round: str, score: Dict[str, Any]) -> None:
        self.set_to_path(f"{room_id}/round_scores/{round}", score)
    
    def get_score_each_round(self, room_id: str, round: str) -> Dict[str, Any]:
        return self.read_from_path(f"{room_id}/round_scores/{round}")
    
    def set_buzzed_player(self, room_id: str, player_name: str) -> None:
        self.set_to_path(f"{room_id}/buzzedPlayer", player_name)
    
    def get_buzzed_player(self, room_id: str) -> str:
        return self.read_from_path(f"{room_id}/buzzedPlayer")
    
    def set_open_buzz(self, room_id: str) -> None:
        self.set_to_path(f"{room_id}/openBuzzed", "open")
    
    def get_open_buzz(self, room_id: str) -> str:
        return self.read_from_path(f"{room_id}/openBuzzed")
    
    def set_star(self, room_id: str, player_name: str) -> None:
        self.set_to_path(f"{room_id}/star", player_name)
    
    def get_star(self, room_id: str) -> str:
        return self.read_from_path(f"{room_id}/star")
    
    def set_show_rules(self, room_id: str, round_number: str) -> None:
        self.set_to_path(f"{room_id}/showRules", {"show": True, "round": round_number})
    
    def get_show_rules(self, room_id: str) -> Dict[str, Any]:
        return self.read_from_path(f"{room_id}/showRules")
    
    def set_used_topics(self, room_id: str, used_topics: List[str]) -> None:
        self.set_to_path(f"{room_id}/usedTopics", used_topics)
    
    def get_used_topics(self, room_id: str) -> List[str]:
        return self.read_from_path(f"{room_id}/usedTopics")
    
    def set_return_to_topic_selection(self, room_id: str, should_return: bool) -> None:
        self.set_to_path(f"{room_id}/returnToTopicSelection", should_return)
    
    def get_return_to_topic_selection(self, room_id: str) -> bool:
        return self.read_from_path(f"{room_id}/returnToTopicSelection")
    
    def set_round_start(self, room_id: str, round_number: str, grid: Optional[List[List[str]]] = None) -> None:
        self.set_to_path(f"{room_id}/rounds", {
        "round": round_number,
        "grid": grid
    })
    
    def set_round_scores(self, room_id: str, round_scores: Dict[str, Any]) -> None:
        self.set_to_path(f"{room_id}/round_scores", round_scores)
    
    def get_round_scores(self, room_id: str) -> Dict[str, Any]:
        return self.read_from_path(f"{room_id}/round_scores")
    
    def send_scores_list(self, room_id: str, scores_list: Dict[str, Any]) -> None:
        self.set_to_path(f"{room_id}/scores", scores_list)
    
    def get_scores(self, room_id: str) -> Dict[str, Any]:
        return self.read_from_path(f"{room_id}/scores")
    
    def set_spectator(self, room_id: str, uid: str) -> None:
        self.set_to_path(f"{room_id}/spectators/{uid}", True)
    
    def get_spectator(self, room_id: str) -> Dict[str, Any]:
        return self.read_from_path(f"{room_id}/spectators")
    
    def delete_spectator(self, room_id: str, uid: str) -> None:
        self.delete_from_path(f"{room_id}/spectators/{uid}")

    def set_next_round(self, room_id: str, round_number: str) -> None:
        self.set_to_path(f"{room_id}/nextRound", round_number)
    
    def set_round_rules(self, room_id: str, round_number: str, rules: Dict[str, Any]) -> None:
        self.set_to_path(f"{room_id}/round_rules/{round_number}", rules)
    
    def get_round_rules(self, room_id: str, round_number: str) -> Dict[str, Any]:
        return self.read_from_path(f"{room_id}/round_rules/{round_number}")
    
    def set_round_2_grid(self, room_id: str, grid: List[List[str]]) -> None:
        self.set_to_path(f"{room_id}/grid", grid)
    
    def set_selected_cell(self,room_id: str, row_index: str, col_index:str):
        self.set_to_path(f"{room_id}/cell", {"rowIndex": row_index, "colIndex": col_index})


    def set_cell_color(self, room_id: str, row_index: str, col_index:str, color: str):
        self.set_to_path(f"{room_id}/color", {"rowIndex": row_index, "colIndex": col_index, "color": color})


    def set_selected_row(self, room_id: str, selected_row_number: str, is_row: bool,word_length: int):
        self.set_to_path(f"{room_id}/select", {"selected_row_number": selected_row_number, "is_row": is_row, "word_length": word_length})

    def set_incorrect_row(self, room_id: str, selected_row_number: str, is_row:bool, word_length: int):
        self.set_to_path(f"{room_id}/incorrect", {"selected_row_number": selected_row_number, "is_row": is_row, "word_length": word_length})

    def set_correct_row(self, room_id: str, selected_row_number: str, correct_answer: str, marked_character_index: str, is_row:bool):
        self.set_to_path(f"{room_id}/correct", {"selected_row_number": selected_row_number, "correct_answer": correct_answer, "marked_character_index": json.loads(marked_character_index), "is_row": is_row})

    def send_answer_to_player(self, answer: str, room_id:str):
        self.set_to_path(f"{room_id}/answers", answer)

    def broadcast_player_answer(self,room_id:str, answers):
        self.set_to_path(f"{room_id}/answerLists", answers)

    def send_currrent_turn_to_player(self, stt:int, room_id:str):
        self.set_to_path(f"{room_id}/turn", stt)

    def send_selected_packet_name_to_player(self, packet:str, room_id:str):
        self.set_to_path(f"{room_id}/selectedPacket", packet)

    def send_packet_name_to_player(self, packet_list:List[str], room_id:str):
        self.set_to_path(f"{room_id}/packets", packet_list)

    def send_question_to_player(self, room_id:str, question: dict):
        self.set_to_path(f"{room_id}/questions", question)

    def send_obstacle(self, room_id:str, obstacle: str, placementArray: List[PlacementArray]):
        logger.info(f"answer {room_id}")
        logger.info(f"obstacle {obstacle}")
        self.set_to_path(f"{room_id}/obstacles",{
            "obstacle": obstacle,
            "placementArray": placementArray
        })

    def start_time(self, room_id:str):
        logger.info(f"room_id {room_id}")
        self.set_to_path(f"{room_id}/times", int(datetime.datetime.utcnow().timestamp() * 1000))

    def show_rules(self, room_id: str, round_number: str):
        self.set_to_path(f"{room_id}/showRules", {
            "show": True,
            "round": round_number
        })


    def hide_rules(self, room_id: str):
        self.delete_path(f"{room_id}/showRules")

    def is_existing_player(self, room_id:str, uid:str):
        return self.read_from_path(f"{room_id}/player_answer/{uid}")
    
    def set_single_player_answer(self, room_id: str, uid: str, player_answer: Dict[str, Any]) -> None:
        self.set_to_path(f"{room_id}/player_answer/{uid}", player_answer)
    
    def get_player_answer(self, room_id: str, uid: str) -> Dict[str, Any]:
        return self.read_from_path(f"{room_id}/player_answer/{uid}")
    
    def get_all_player_answer(self, room_id: str) -> List[Dict[str, Any]]:
        return self.read_from_path(f"{room_id}/player_answer")
    
    def get_current_correct_answer(self,room_id: str):
        return self.read_from_path(f"{room_id}/current_correct_answer")

    def update_score_each_round(self,room_id: str, data: Dict[str, Any], round: str) -> None:
        logger.info(f"Setting round scores data for room {room_id}, round {round}: {data}")
        self.set_to_path(f"{room_id}/round_scores/{round}", data)


    #Buzz repo
    def buzz_first(self, room_id:str, player_name: str):

        def transaction_update(current_value):
            if current_value is None:
                return player_name
            return current_value 
        
        result = self.do_transaction(f"{room_id}/buzzedPlayer", transaction_update)

        if result == player_name:
            return True
        else:
            return False
        
    def reset_buzz(self,room_id: str):
        self.delete_path(f"{room_id}/buzzedPlayer")

    def open_buzz(self, room_id: str):
        self.set_to_path(f"{room_id}/openBuzzed", "open")

    def close_buzz(self, room_id: str):
        self.delete_path(f"{room_id}/openBuzzed")

    #Room repo
    def get_players_in_room(self, room_id: str):
        return self.read_from_path(f"{room_id}/players")
    
    def set_player_to_room(self, room_id: str, uid:str, player):
        self.set_to_path(f"{room_id}/players/{uid}", player)

    def set_spectator_to_room(self, room_id:str):
        return self.set_to_path_with_child_node(f"{room_id}/spectators", True)


    


        


    



    
    
    

    
