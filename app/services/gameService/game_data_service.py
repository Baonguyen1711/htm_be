from typing import Any, Dict, List, Optional
from fastapi import HTTPException, logger
from firebase_admin import db

from ...models.scores import Score, ScoreRule

from ...util.string_processing import normalize_string
from ...repositories.realtimedb.game_repository import GameRepository
from ..test_service import TestService
from ...models.questions import Answer, Grid, PlacementArray
from ...models.scores import  ScoreRule
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class GameDataService:
    def __init__(self, game_repository: GameRepository, test_service: TestService):
        self.game_repository = game_repository
        self.test_service = test_service


    def send_grid(self, room_id: str, grid: Grid):
        self.game_repository.set_round_2_grid(room_id, grid.grid)

    def send_selected_cell(self, room_id: str, row_index: str, col_index:str):
        self.game_repository.set_selected_cell(room_id, row_index, col_index)

    def send_cell_color(self, room_id: str,row_index:str, col_index:str, color:str):
        self.game_repository.set_cell_color(room_id,row_index,col_index, color)

    def send_selected_row(self, room_id:str, selected_row_number:str, is_row: bool, word_length:int):
        self.game_repository.set_selected_row(room_id, selected_row_number, is_row, word_length)

    def send_correct_row(self,room_id: str, selected_row_number: str, correct_answer: str, marked_character_index: str, is_row:bool):
        self.game_repository.set_correct_row(room_id, selected_row_number, correct_answer, marked_character_index, is_row)
        
    def send_incorrect_row_to_player(self,room_id: str, selected_row_number: str, is_row:bool, word_length: int):
        self.game_repository.set_incorrect_row(room_id,selected_row_number,is_row,word_length)
        
    def send_answer_to_player(self, answer: str, room_id:str):
        self.game_repository.send_answer_to_player(answer, room_id)

    def send_selected_packet_name_to_player(self, packet:str, room_id:str):
        self.game_repository.send_selected_packet_name_to_player(packet, room_id)

    def send_packet_name_to_player(self, packet_list:List[str], room_id:str):
        self.game_repository.send_packet_name_to_player(packet_list, room_id)

    def send_question_to_player(self, room_id:str, question: dict):
        self.game_repository.send_question_to_player( room_id,question)

    def send_obstacle(self, room_id:str, obstacle: str, placementArray: List[PlacementArray]):
        self.game_repository.send_obstacle(room_id,obstacle, placementArray)

    def set_score_rules(self, room_id: str, rules: ScoreRule) -> None:
        self.game_repository.set_score_rules(room_id, rules)
    
    def set_score(self, room_id: str, score: Dict[str, Any]) -> None:
        self.game_repository.set_score(room_id, score)
       
    def set_round_scores(self, room_id: str, round_scores: Dict[str, Any]) -> None:
        self.game_repository.set_round_scores(room_id, round_scores)    
    
    def set_used_topics(self, room_id: str, used_topics: List[str]) -> None:
        self.game_repository.set_used_topics(room_id, used_topics)

    def set_show_rules(self, room_id: str, round_number: str) -> None:
        self.game_repository.set_show_rules(room_id, round_number)

    def set_spectator(self, room_id: str, uid: str) -> None:
        self.game_repository.set_spectator(room_id, uid)

    def set_buzzed_player(self, room_id: str, player_name: str) -> None:
        self.game_repository.set_buzzed_player(room_id, player_name)

    def set_single_player_answer(self, room_id: str, uid: str, player_answer: Dict[str, Any]):
        self.game_repository.set_single_player_answer(room_id, uid, player_answer)
    

    #GET 
    def get_round_scores(self, room_id: str) -> Dict[str, Any]:
        return self.game_repository.get_round_scores(room_id)

    def get_score(self, room_id: str) -> Dict[str, Any]:
        return self.game_repository.get_score(room_id)

    def get_score_rules(self, room_id: str) -> Dict[str, Any]:
        return self.game_repository.get_score_rules(room_id)

    def get_score_each_round(self, room_id: str, round: str) -> Dict[str, Any]:
        return self.game_repository.get_score_each_round(room_id, round)
    
    def get_spectator(self, room_id: str) -> Dict[str, Any]:
        return self.game_repository.get_spectator(room_id)
    
    def get_player_answer(self, room_id, uid):
        return self.game_repository.get_player_answer(room_id, uid)
    
    def get_current_correct_answer(self,room_id: str):
        return self.game_repository.get_current_correct_answer(room_id)
    
    def get_all_player_answer(self, room_id: str) -> List[Dict[str, Any]]:
        return self.game_repository.get_all_player_answer(room_id)
    
    def is_existing_player(self, room_id:str, uid:str):
        return self.game_repository.is_existing_player(room_id,uid )
    

    
    #DELETE
    def delete_spectator(self, room_id: str, uid: str) -> None:
        self.game_repository.delete_spectator(room_id,uid)

    def submit_answer(self,room_id: str, uid: str, answer: Answer):

        player_answer = self.get_player_answer(room_id, uid)

        logger.info(f"player {player_answer}")
        current_correct_answer = self.get_current_correct_answer(room_id)           
        submitted = normalize_string(answer.answer)

        logger.info(f"player answer {player_answer}")
        logger.info(f"submit {submitted}")
        logger.info(f"correcrt {current_correct_answer}")

        player_answer["answer"] = answer.answer
        player_answer["time"] = float(answer.time)

        if any(submitted == normalize_string(correct_answer) for correct_answer in current_correct_answer):
            logger.info(f"submit {submitted}")
            player_answer["is_correct"] = True

        logger.info(f"player_answer {player_answer}")

        self.set_single_player_answer(room_id, uid, player_answer)

    def obstacle_score(self,room_id: str, is_obstacle_correct: bool, player_answer, stt: str, obstacle_point: int, score_list: List):
        if is_obstacle_correct:
            for player in player_answer:
                if player["stt"] == stt:
                    player["score"] += obstacle_point
                    player["round_scores"][int(round)] += obstacle_point
                    player["is_correct"] = True  # Set this player as correct
                    self.set_single_player_answer(room_id, player["uid"], player)
                    logger.info(f"[Round4-Main] {player['uid']} +{obstacle_point}")

            for player in player_answer:
                score_list.append({
                    "playerName": player["userName"],
                    "avatar": player["avatar"],
                    "score": player["score"],
                    "isCorrect": player["is_correct"],  # Send as boolean
                    "isModified": player["is_correct"] if round != "3" else False,  
                    "stt": player["stt"]
                })

    def adaptive_score(self, room_id:str, round: str, player_answers, score_list: List):
        current_correct_answer = self.get_current_correct_answer(room_id)
        logger.info(f"Current correct answers: {current_correct_answer}")
        logger.info(f"player_answers inside adaptive {player_answers}")

        # Set is_correct for players who actually answered correctly
        for player in player_answers:
            if player.get("answer"):
                submitted = normalize_string(player["answer"])
                if any(submitted == normalize_string(correct_answer) for correct_answer in current_correct_answer):
                    player["is_correct"] = True
                    self.set_single_player_answer(room_id, player["uid"], player)
                    logger.info(f"Player {player['uid']} answered correctly: {player['answer']}")

        correct_players = [p for p in player_answers if p.get("is_correct") == True]
        correct_count = len(correct_players)

        if correct_count == 4:
            points = 5
        elif correct_count == 3:
            points = 10
        elif correct_count == 2:
            points = 15
        elif correct_count == 1:
            points = 20
        else:
            points = 0

        logger.info(f"[Round {round} - correct_count_bonus] {correct_count} correct players, awarding {points} points each")

        for player in correct_players:
            logger.info(f'player["round_scores"] {player["round_scores"]}')
            player["score"] += points
            player["round_scores"][int(round)] = player["round_scores"][int(round)] + points
            logger.info(f"[Round {round} - correct_count_bonus] {player['uid']} +{points}")
            self.set_single_player_answer(room_id, player["uid"], player)

        for player in player_answers:
            score_list.append({
                "playerName": player["userName"],
                "avatar": player["avatar"],
                "score": player["score"],
                "isCorrect": player["is_correct"],  # Send as boolean
                "isModified": player["is_correct"] if round != "3" else False, 
                "stt": player["stt"]
            })

    def auto_score(self, player_answer, room_id: str, round: str, stt: str,is_correct: bool, score_rules: Any, round_4_mode: str, difficulty: str, is_take_turn_correct: bool, stt_take_turn: str, stt_taken: str, score_list: List ):
                
        logger.info("Attempting to submit answer")
        correct_players = sorted(
            [p for p in player_answer if p.get("is_correct") == True],
            key=lambda x: x["time"]
        )

        logger.info(f"correct_players {correct_players}")

        # no flashing for round 3
        if round == "3" and stt and is_correct and is_correct.lower() == "true":
            matched_player = next(
                (p for p in player_answer if p["stt"] == stt),
                None
            )
            if matched_player:
                matched_player["score"] += score_rules[f"round{round}"]
                matched_player["round_scores"][int(round)] += score_rules[f"round{round}"]
                
                self.set_single_player_answer(room_id, matched_player["uid"], matched_player)
                logger.info(f"Updated player {matched_player['uid']} score for round 3")

        if round == "4" and round_4_mode and difficulty:
            logger.info(f"difficulty {difficulty}")
            diff_index = {"Dễ": 0, "Trung bình": 1, "Khó": 2}.get(difficulty)
            if diff_index is None:
                raise HTTPException(status_code=400, detail="Invalid difficulty")

            points = score_rules["round4"][diff_index]

            if round_4_mode == "main":
                for player in player_answer:
                    if player["stt"] == stt:
                        player["score"] += points
                        player["round_scores"][int(round)] += points
                        self.set_single_player_answer(room_id, player["uid"], player)
                        logger.info(f"[Round4-Main] {player['uid']} +{points}")

            elif round_4_mode == "nshv":
                for player in player_answer:
                    if player["stt"] == stt:
                        if is_correct == "true":
                            added = int(points * 1.5)
                            player["score"] += added
                            player["round_scores"][int(round)] += added
                            self.set_single_player_answer(room_id, player["uid"], player)
                            logger.info(f"[Round4-NSHV] {player['uid']} +{added}")
                        if is_correct == "false":
                            deducted = points 
                            player["score"] -= deducted
                            player["round_scores"][int(round)] -= deducted
                            player["was_deducted_this_round"] = True
                            self.set_single_player_answer(room_id, player["uid"], player)
                            logger.info(f"[Round4-NSHV] {player['uid']} -{deducted}")

            elif round_4_mode == "take_turn":
                if is_take_turn_correct == "false":
                    for player in player_answer:
                        if player["stt"] == stt_take_turn:
                            deducted = points // 2
                            player["score"] = max(0, player["score"] - deducted)
                            player["round_scores"][int(round)] -= deducted
                            self.set_single_player_answer(room_id, player["uid"], player)
                            logger.info(f"[Round4-TakeTurn-False] {player['uid']} -{deducted}")
                elif is_take_turn_correct == "true":
                    taker = next((p for p in player_answer if p["stt"] == stt_take_turn), None)
                    taken = next((p for p in player_answer if p["stt"] == stt_taken), None)

                    if taker and taken:
                        if not taken.get("was_deducted_this_round"):                
                            deducted = points 
                            taken["score"] = max(0, taken["score"] - deducted)
                            taken["round_scores"][int(round)] -= deducted
                            self.set_single_player_answer(room_id, taken["uid"], taken)
                            taker["score"] += points
                            taker["round_scores"][int(round)] +=points
                            self.set_single_player_answer(room_id, taker["uid"], taker)
                            logger.info(f"[Round4-TakeTurn-True] {taker['uid']} +{points}, {taken['uid']} -{deducted}")

            else:
                raise HTTPException(status_code=400, detail="Invalid round_4_mode")


        if round in ["1", "2"]:
            current_correct_answer = self.get_current_correct_answer(room_id)
            logger.info(f"Current correct answers for manual scoring: {current_correct_answer}")

            # Set is_correct for players who actually answered correctly
            for player in player_answer:
                if player.get("answer"):
                    submitted = normalize_string(player["answer"])
                    if any(submitted == normalize_string(correct_answer) for correct_answer in current_correct_answer):
                        player["is_correct"] = True
                        self.set_single_player_answer(room_id, player["uid"], player)
                        logger.info(f"Player {player['uid']} answered correctly: {player['answer']}")

        correct_players = [p for p in player_answer if p.get("is_correct") == True]

        for player in player_answer:
            # Check if this player is correct this round
            # Only apply manual scoring for rounds 1 and 2
            if player["is_correct"] and round in ["1", "2"]:
                index = next((i for i, p in enumerate(correct_players) if p["uid"] == player["uid"]), None)
                bonus = score_rules[f"round{round}"][index] if index is not None else 0
                player["score"] += bonus
                player["round_scores"][int(round)] += bonus
                self.set_single_player_answer(room_id, player["uid"], player)

            score_list.append({
                "playerName": player["userName"],
                "avatar": player["avatar"],
                "score": player["score"],
                "isCorrect": player["is_correct"],  # Send as boolean
                "isModified": player["is_correct"] if round != "3" else False,  # No flashing for Round 3
                "stt": player["stt"]
            })

    def reset_score_list(self, room_id: str, player_answer):
        for player in player_answer:
            player["is_correct"] = False
            player["was_deducted_this_round"] = False
            player["time"] = None
            # Don't call set_player_answer here - it would overwrite the flash state
            logger.info(f"Reset player {player['uid']} for next round")

        # Send scores without flashing when round ends
        score_list = []
        for player in player_answer:
            score_list.append({
                "playerName": player["userName"],
                "avatar": player["avatar"],
                "score": player["score"],
                "isCorrect": False,  # Reset to false (boolean)
                "isModified": False,  # No flashing during round transition (boolean)
                "stt": player["stt"]
            })
        self.game_repository.send_scores_list(room_id, score_list)

    def update_each_round_score(self, room_id: str, round: str, player_answer):
        firebase_data = {
            player["stt"]: {
                "playerName": player["userName"],
                "avatar": player["avatar"],
                "roundScore": player["round_scores"][int(round)]
            }
            for player in player_answer
        }
        self.game_repository.update_score_each_round(room_id,firebase_data,round)

    def score(
            self,
            room_id: str, 
            mode: str,
            scores: Optional[List[Score]] = None, 
            round: Optional[str] = None, 
            stt: Optional[str] = None,
            is_obstacle_correct: Optional[str] = None,
            obstacle_point: Optional[int] = None,
            is_correct: Optional[str] = None,
            round_4_mode: Optional[str] = None,
            difficulty: Optional[str] = None,
            is_take_turn_correct: Optional[str] = None,
            stt_take_turn: Optional[str] = None,
            stt_taken: Optional[str] = None 
        ):
        score_list = []
        score_rules = self.get_score_rules(room_id)
        player_answers = self.get_all_player_answer(room_id)
        player_answer_list = list(player_answers.values())
        logger.info(f"player answer in scoring {player_answer_list}")

        # Reset all players' is_correct to False at the start of scoring
        for player_answer in player_answer_list:
            logger.info(f"player_answer {player_answer}")
            player_answer["is_correct"] = False
            self.set_single_player_answer(room_id, player_answer["uid"], player_answer_list)
        
        self.obstacle_score(room_id, is_obstacle_correct, player_answer_list, stt, obstacle_point, score_list)
            
        if mode == "manual" and not is_obstacle_correct:
            for score in scores:
                score_list.append({
                    "playerName": score.playerName,
                    "avatar": score.avatar,
                    "score": score.score,
                    "isCorrect": score.isCorrect,
                    "isModified": score.isModified,
                    "stt": score.stt
                })

        if mode == "adaptive" and round in ["1", "2"] and not is_obstacle_correct:
            self.adaptive_score(room_id, round, player_answer_list, score_list)            

        if mode == "auto" and not is_obstacle_correct:
            self.auto_score(player_answer_list, room_id, round, stt, is_correct, score_rules, round_4_mode, difficulty, is_take_turn_correct, stt_take_turn, stt_taken, score_list)
    
        score_ref = db.reference(f"rooms/{room_id}/scores")
        score_ref.set(score_list)
        #self.game_repository.send_scores_list(room_id, score_list)

        self.reset_score_list(room_id, player_answer_list)

        self.update_each_round_score(room_id, round, player_answer_list)

    def broadcast_player_answer(self, room_id: str, answer_list: List[Answer]):
        self.game_repository.broadcast_player_answer(room_id, answer_list)


       
    
