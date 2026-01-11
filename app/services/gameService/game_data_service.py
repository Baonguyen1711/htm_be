from typing import Any, Dict, List, Optional
from fastapi import HTTPException, logger, Depends
from firebase_admin import db

from app.models.state import GameState

from ...models.scores import Score, ScoreRule

from ...util.string_processing import normalize_string
from ...repositories.realtimedb.game_repository import GameRepository
from ...repositories.firestore.statistics_repository import StatisticsRepository
from ..test_service import TestService
from ...models.questions import Answer, Grid, PlacementArray
from ...models.scores import ScoreRule
# FIXED: Import from service_dependencies to break circular import
from ...dependencies.service_dependencies import get_game_repository, get_test_service, get_statistics_repository
import logging
from ...helper.global_variable import is_key_exist_in_dict, group_id_list
from ...helper.time import now_ms
from ...constants.game_constants import MULTIPLAYER_QUESTION_TIME, MULTIPLAYER_SCORING_TIME_LAPSE
from ...constants.gemini_prompt import IS_ACCEPTED_ANSWER_PROMPT
from ...util.gemini import prompting
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class GameDataService:
    def __init__(self, game_repository: GameRepository,test_service: TestService,statistics_repository: StatisticsRepository):

        self.game_repository = game_repository
        self.test_service = test_service
        self.statistics_repository = statistics_repository

    def send_specific_question_to_player(self, uid: str, test_name: str, room_id: str, round: Optional[str] = None, packet_name: Optional[str] = None, difficulty: Optional[str] = None, question_number: Optional[int] | None= None, page: Optional[int] | None = None, limit: Optional[int] | None = None):
        test_data = self.test_service.process_test_data(uid, test_name)
        logger.info(f"test_data {test_data}")

        question = self.test_service.get_specific_question(test_data,round,packet_name, difficulty, question_number=question_number, page=page, limit=limit)
        question_without_answer = self.test_service.get_question_without_answer(question, room_id)
        logger.info(f"question {question}")
        logger.info(f"question_without_answer {question_without_answer}")
        self.send_question_to_player(room_id,question_without_answer)
        return question

    def send_grid(self, room_id: str, grid: List[List[str]], marked_characters_index):
        self.game_repository.set_round_2_grid(room_id, grid, marked_characters_index)

    def send_selected_cell(self, room_id: str, row_index: str, col_index:str):
        self.game_repository.set_selected_cell(room_id, row_index, col_index)

    def send_cell_color(self, room_id: str,row_index:str, col_index:str, color:str):
        self.game_repository.set_cell_color(room_id,row_index,col_index, color)

    def send_selected_row(self, room_id:str, selected_row_number:str, is_row: bool, word_length:int,selected_row_index: int, selected_col_index: int):
        self.game_repository.set_selected_row(room_id, selected_row_number, selected_row_index, selected_col_index,  is_row, word_length)

    def send_correct_row(self,room_id: str, selected_row_number: str, correct_answer: str, marked_character_index: str, is_row:bool, selected_row_index: int, selected_col_index: int):
        self.game_repository.set_correct_row(room_id, selected_row_number, selected_row_index, selected_col_index,  correct_answer, marked_character_index, is_row)
        
    def send_incorrect_row_to_player(self,room_id: str, selected_row_number: str, is_row:bool, word_length: int, selected_row_index: int, selected_col_index: int):
        self.game_repository.set_incorrect_row(room_id,selected_row_number, selected_row_index, selected_col_index, is_row,word_length)
        
    def send_answer_to_player(self, room_id:str):
        current_correct_answer = self.game_repository.get_current_correct_answer(room_id)
        logger.info(f"current_correct_answer {current_correct_answer}")
        self.game_repository.send_answer_to_player(current_correct_answer, room_id)

    def send_selected_packet_name_to_player(self, packet:str, room_id:str):
        self.game_repository.send_selected_packet_name_to_player(packet, room_id)

    def send_packet_name_to_player(self, packet_list:List[str], room_id:str):
        self.game_repository.send_packet_name_to_player(packet_list, room_id)

    def send_used_packet_name_to_player(self, used_packet_list:List[str], room_id:str):
        self.game_repository.set_used_packets(room_id, used_packet_list)

    def send_should_return_to_packet_selection(self, should_return:bool, room_id:str):
        self.game_repository.set_return_to_topic_selection(room_id, should_return)

    def send_question_to_player(self, room_id:str, question: dict):
        self.game_repository.send_question_to_player( room_id,question)

    def send_obstacle(self, room_id:str, grid: Grid):
        self.game_repository.send_obstacle(room_id,grid)

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

    def reset_player_answer(self, room_id: str):
        logger.info(f"reset player answer")
        current_player_answer_list = self.game_repository.get_player_answer_list(room_id)
        logger.info(f"current_player_answer_list {current_player_answer_list}")
        if current_player_answer_list is None:
            return
        
        for player in current_player_answer_list:
            player["answer"] = ""
            player["is_correct"] = False
            player["time"] = 0

        self.game_repository.broadcast_player_answer(room_id, current_player_answer_list)

    def get_next_question(self, uid: str, test_name: str, room_id: str, round: Optional[str] = None, packet_name: Optional[str] = None, difficulty: Optional[str] = None, question_number: Optional[int] | None= None, page: Optional[int] | None = None, limit: Optional[int] | None = None ):
        current_state = self.game_repository.get_current_game_state(room_id)

        current_question_index = (
            current_state.get("currentQuestion", 0)
            if current_state
            else 0
        )
        
        next_question_index = current_question_index + 1

        self.send_specific_question_to_player(
            uid=uid,
            test_name=test_name,
            room_id=room_id,
            round=round,
            question_number=next_question_index
        )

        self.game_repository.update_game_state(room_id, {
            "currentQuestion": next_question_index,
            "phase": "QUESTION"
        })



    def update_game_state(self, room_id: str, state: GameState):
        logger.info(f"state {state}")

        # 1 is the signal for time starting
        if state.get("phaseStartTime") is not None and state.get("phaseStartTime") == 1:
            state["phaseStartTime"] = now_ms()

        # update_data = state.model_dump(exclude_none=True)

        # logger.info(f"update_data{update_data}")

        self.game_repository.update_game_state(room_id, state)

    

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
    
    def get_current_correct_answer_value(self,room_id: str):
        return self.game_repository.get_current_correct_answer_value(room_id)
    
    def get_all_player_answer(self, room_id: str) -> List[Dict[str, Any]]:
        return self.game_repository.get_all_player_answer(room_id)
    
    def is_existing_player(self, room_id:str, uid:str):
        return self.game_repository.is_existing_player(room_id,uid )
    

    
    #DELETE
    def delete_spectator(self, room_id: str, uid: str) -> None:
        self.game_repository.delete_spectator(room_id,uid)

    def submit_answer(self,room_id: str, uid: str, answer: Answer):

        player_answer = self.get_player_answer(room_id, uid)

        if not player_answer:
            return 

        logger.info(f"player {player_answer}")
        current_correct_answer = self.get_current_correct_answer(room_id)        
        current_question = self.game_repository.get_current_question(room_id)["question"]   
        logger.info(f"current_question {current_question}")
        submitted = normalize_string(answer.answer)

        logger.info(f"player answer {player_answer}")
        logger.info(f"submit {submitted}")
        logger.info(f"correcrt {current_correct_answer}")

        player_answer["answer"] = answer.answer
        player_answer["time"] = float(answer.time)

        if any(submitted == normalize_string(correct_answer) for correct_answer in current_correct_answer):
            logger.info(f"submit {submitted}")
            player_answer["is_correct"] = True
        else:
            is_correct = prompting(IS_ACCEPTED_ANSWER_PROMPT.replace("{question}", current_question).replace("{answer}", answer.answer))
            logger.info(f"IS_ACCEPTED_ANSWER_PROMPT: {IS_ACCEPTED_ANSWER_PROMPT}")
            logger.info(f"is_correct prompt: {is_correct}")
            if is_correct == "True":
                player_answer["is_correct"] = True

        logger.info(f"player_answer {player_answer}")

        self.set_single_player_answer(room_id, uid, player_answer)

    def multiplayer_submit_answer(self,room_id: str, uid: str, answer: Answer, test_name: str, group_id: Optional[str] = None):
        logger.info("Attempting to submit multiplayer answer")
        logger.info(f"room_id: {room_id}, uid: {uid}, answer: {answer}, group_id: {group_id}")

        player_answer = self.get_player_answer(room_id, uid)
        logger.info(f"player_answer at start{player_answer}")

        # if group_id is not None:
        #     player_answer = self.game_repository.read_from_path(f"{room_id}/player_answer/{group_id}")

        # if not player_answer:
        #     return 

        logger.info(f"player after {player_answer}")
        # player_answer["is_correct"] = False  
        current_correct_answer = self.get_current_correct_answer(room_id)    
        current_correct_answer_value = self.get_current_correct_answer_value(room_id)         
        submitted = normalize_string(answer.answer)
        answer_list = player_answer["answers"] if "answers" in player_answer else []
        current_question = self.game_repository.get_current_question(room_id)["question"] 
        # submitted_player_group_id = ""
        # for key, value in group_id_list[f"{room_id}"].items():
        #     if uid in value:
        #         submitted_player_group_id = key
        #         break
        #answer_list.append(answer.answer)
        logger.info(f"player answer {player_answer}")
        logger.info(f"submit {submitted}")
        logger.info(f"correcrt {current_correct_answer}")

        player_answer["answer"] = answer.answer
        player_answer["time"] = float(answer.time)
        if group_id is not None:
            player_answer["group_id"] = group_id
        
        if any(submitted == normalize_string(correct_answer) for correct_answer in current_correct_answer):
            logger.info(f"submit {submitted}")
            score = (MULTIPLAYER_QUESTION_TIME//MULTIPLAYER_SCORING_TIME_LAPSE-((player_answer["time"]//MULTIPLAYER_SCORING_TIME_LAPSE)))*MULTIPLAYER_SCORING_TIME_LAPSE
            logger.info(f"score {score}")
            logger.info(f"MULTIPLAYER_QUESTION_TIME {MULTIPLAYER_QUESTION_TIME}")
            logger.info(f"MULTIPLAYER_SCORING_TIME_LAPSE {MULTIPLAYER_SCORING_TIME_LAPSE}")
            logger.info(f"player_answer[time] {player_answer['time']}")
            player_answer["is_correct"] = True
            # if group_id is not None:
            #     player_answer["score"] += score 
            if group_id is not None:
                player_answer["score"] += score // len(player_answer["uid"])

            else:
                player_answer["score"] += score
        else:
            is_correct = prompting(IS_ACCEPTED_ANSWER_PROMPT.replace("{question}", current_question).replace("{answer}", answer.answer))
            logger.info(f"IS_ACCEPTED_ANSWER_PROMPT: {IS_ACCEPTED_ANSWER_PROMPT}")
            logger.info(f"is_correct prompt: {is_correct}")
            logger.info(f"submitted {submitted}")
            logger.info(f"current_question {current_question}") 
            if is_correct == "True":
                logger.info(f"submit {submitted}")
                score = (MULTIPLAYER_QUESTION_TIME//MULTIPLAYER_SCORING_TIME_LAPSE-((player_answer["time"]//MULTIPLAYER_SCORING_TIME_LAPSE)))*MULTIPLAYER_SCORING_TIME_LAPSE
                logger.info(f"score {score}")
                logger.info(f"MULTIPLAYER_QUESTION_TIME {MULTIPLAYER_QUESTION_TIME}")
                logger.info(f"MULTIPLAYER_SCORING_TIME_LAPSE {MULTIPLAYER_SCORING_TIME_LAPSE}")
                logger.info(f"player_answer[time] {player_answer['time']}")
                player_answer["is_correct"] = True
                # if group_id is not None:
                #     player_answer["score"] += score 
                if group_id is not None:
                    player_answer["score"] += score // len(player_answer["uid"])

                else:
                    player_answer["score"] += score
            else:
                player_answer["is_correct"] = False
                
        self.statistics_repository.add_statistics(
            uid,
            test_name,
            {
                "question": current_question,
                "answer": submitted,
                "correct_answer": current_correct_answer_value,
                "is_correct": player_answer["is_correct"]
            }
        )
        answer_list.append({
            "answer": answer.answer,
            "isCorrect": player_answer["is_correct"]
        })

        logger.info(f"player_answer after {player_answer}")

        player_answer["answers"] = answer_list
        logger.info(f"answer_list {answer_list}")
        if group_id is not None:
            self.set_single_player_answer(room_id, group_id, player_answer)
        else:
            self.set_single_player_answer(room_id, uid, player_answer)

    def trigger_scoreboard(self, room_id: str, question_number: int):
        logger.info(f"Triggering scoreboard for room {room_id}, q{question_number}")
        player_answer = self.get_all_player_answer(room_id)
        logger.info(f"player_answer {player_answer}")
        score_list = []
        for player in player_answer.values():
            logger.info(f"player {player}")
            if "groupId" in player:
                score_list.append({
                "playerName": player["userName"],
                "avatar": player["avatar"],
                "score": player["score"],
                "isCorrect": player["is_correct"],  # Send as boolean
                "isModified": player["is_correct"] if round != "3" else False,  # No flashing for Round 3
                "stt": player["stt"],
                "uid": player["uid"],
                "groupId": player["groupId"]
            })
                
                logger.info(f"score_list {score_list}")
            else:
                score_list.append({
                    "playerName": player["userName"],
                    "avatar": player["avatar"],
                    "score": player["score"],
                    "isCorrect": player["is_correct"],  # Send as boolean
                    "isModified": player["is_correct"] if round != "3" else False,  # No flashing for Round 3
                    "stt": player["stt"],
                    "uid": player["uid"]
                })

        self.game_repository.send_score_list(room_id, score_list)

    def obstacle_score(self,room_id: str, is_obstacle_correct: bool, player_answer, stt: str, obstacle_point: int, score_list: List, round: str):
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
                "stt": player["stt"],
                "uid": player["uid"]
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
                    logger.info(f"taker {taker}")
                    logger.info(f"taken {taken}")


                    if taker and taken:
                        if not taken.get("was_deducted_this_round"):                
                            deducted = points 
                            taken["score"] = max(0, taken["score"] - deducted)
                            taken["round_scores"][int(round)] -= deducted
                            self.set_single_player_answer(room_id, taken["uid"], taken)
                            logger.info(f"[Round4-TakeTurn-True] {taken['uid']} -{deducted}")
                        taker["score"] += points
                        taker["round_scores"][int(round)] +=points
                        self.set_single_player_answer(room_id, taker["uid"], taker)
                        logger.info(f"[Round4-TakeTurn-True] {taker['uid']} +{points}")

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
                "stt": player["stt"],
                "uid": player["uid"]
            })

    def reset_score_list(self, room_id: str, player_answer):
        logger.info(f"player_answer before reset {player_answer}")
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
                "stt": player["stt"],
                "uid": player["uid"]
            })
        self.game_repository.send_score_list(room_id, score_list)

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
            self.set_single_player_answer(room_id, player_answer["uid"], player_answer)
        
        self.obstacle_score(room_id, is_obstacle_correct, player_answer_list, stt, obstacle_point, score_list, round)
            
        if mode == "manual" and not is_obstacle_correct:
            logger.info(f"Scores in manual scoring: {scores}")
            for score in scores:
                score_list.append({
                    "playerName": score.playerName,
                    "avatar": score.avatar,
                    "score": score.score,
                    "isCorrect": score.isCorrect,
                    "isModified": score.isModified,
                    "stt": score.stt,
                    "uid": score.uid
                })

                for player in player_answer_list:
                    if player["stt"] == score.stt:
                        player["score"] = score.score
                        player["round_scores"][int(round)] = score.score
                        player["is_correct"] = score.isCorrect
                        self.set_single_player_answer(room_id, player["uid"], player)

            self.game_repository.send_score_list(room_id, score_list)
            score_list_after_setting = self.game_repository.get_score_list(room_id)
            logger.info(f"score_list_after_setting: {score_list_after_setting}")
            return

        if mode == "adaptive" and round in ["1", "2"] and not is_obstacle_correct:
            self.adaptive_score(room_id, round, player_answer_list, score_list)            

        if mode == "auto" and not is_obstacle_correct:
            self.auto_score(player_answer_list, room_id, round, stt, is_correct, score_rules, round_4_mode, difficulty, is_take_turn_correct, stt_take_turn, stt_taken, score_list)
    
        logger.info(f"Score list before setting scoring: {score_list}")
        self.game_repository.send_score_list(room_id, score_list)
        score_list_after_setting = self.game_repository.get_score_list(room_id)
        logger.info(f"score_list_after_setting: {score_list_after_setting}")

        self.reset_score_list(room_id, player_answer_list)

        self.update_each_round_score(room_id, round, player_answer_list)

    def broadcast_player_answer(self, room_id: str, answer_list: List[Answer]):
        self.game_repository.broadcast_player_answer(room_id, answer_list)

    def create_practice_room(self, room_id: str, room_data: Dict[str, Any]) -> None:
        self.game_repository.create_practice_room(room_id, room_data)

    def join_group_invite(self, room_id: str, group_id: str, uid: str, inviter_uid: str) -> None:
        logger.info(f"Joining group invite: room_id={room_id}, group_id={group_id}, uid={uid}, inviter_uid={inviter_uid}")
        target_player = self.game_repository.find_object_in_path_by_field(f"{room_id}/scores", "uid", uid)
        inviter_player = self.game_repository.find_object_in_path_by_field(f"{room_id}/scores", "uid", inviter_uid)


        logger.info(f"target_player {target_player}")
        logger.info(f"inviter_player {inviter_player}")

        target_player_answer = self.game_repository.read_from_path(f"{room_id}/player_answer/{uid}")
        inviter_player_answer = self.game_repository.read_from_path(f"{room_id}/player_answer/{inviter_uid}")

        logger.info(f"target_player_answer {target_player_answer}")
        logger.info(f"inviter_player_answer {inviter_player_answer}")

        
        if not target_player:
            raise ValueError(f"Player with uid={uid} not found in room {room_id}")
        
        target_player_key, target_player_data = next(iter(target_player.items()))
        if inviter_player:
            inviter_player_key, inviter_player_data = next(iter(inviter_player.items()))
        logger.info(f"target_player_key {target_player_key}")
        logger.info(f"target_player_data {target_player_data}")


        target_group = self.game_repository.find_object_in_path_by_field(f"{room_id}/scores", "groupId", group_id)
        target_group_player_answer = self.game_repository.read_from_path(f"{room_id}/player_answer/{group_id}")

        logger.info(f"target_group_player_answer {target_group_player_answer}")
        logger.info(f"target_group {target_group}")

        if not target_group:
            
            self.game_repository.update_node_path(f"{room_id}/scores/{target_player_key}",{
                "groupId": group_id,
                "uid": [target_player_data["uid"], inviter_player_data["uid"]],
                "playerName": [target_player_data["playerName"], inviter_player_data["playerName"]],
                "avatar": [target_player_data["avatar"], inviter_player_data["avatar"]],
            })

            self.game_repository.update_node_path(f"{room_id}/player_answer/{group_id}",{
                **target_player_answer,
                "uid": [target_player_data["uid"], inviter_player_data["uid"]],
                "userName": [target_player_data["playerName"], inviter_player_data["playerName"]],
                "avatar": [target_player_data["avatar"], inviter_player_data["avatar"]],
                "groupId": group_id
            })

            self.game_repository.delete_data_from_a_score_list_node(room_id, inviter_player_key)
            self.game_repository.delete_path(f"{room_id}/player_answer/{inviter_uid}")
            self.game_repository.delete_path(f"{room_id}/player_answer/{uid}")
            
        else:
            target_group_key, target_group_data = next(iter(target_group.items()))

            uids = target_group_data.get("uid", [])
            player_names = target_group_data.get("playerName", [])
            avatars = target_group_data.get("avatar", [])

            if not isinstance(uids, list):
                uids = [uids]
            if not isinstance(player_names, list):
                player_names = [player_names]
            if not isinstance(avatars, list):
                avatars = [avatars]

            uids.append(target_player_data["uid"])
            player_names.append(target_player_data["playerName"])
            avatars.append(target_player_data["avatar"])

            self.game_repository.update_node_path(
                f"{room_id}/scores/{target_group_key}",
                {
                    "uid": uids,
                    "playerName": player_names,
                    "avatar": avatars,
                }
            )

            self.game_repository.update_node_path(
                f"{room_id}/player_answer/{group_id}",
                {
                    **target_group_player_answer,
                    "uid": uids,
                    "userName": player_names,
                    "avatar": avatars,
                }
            )

            self.game_repository.delete_data_from_a_score_list_node(room_id, target_player_key)
            # self.game_repository.delete_path(f"{room_id}/player_answer/{inviter_uid}")
            self.game_repository.delete_path(f"{room_id}/player_answer/{uid}")


    def set_round_mapping(self, room_id: str, round_mapping: Any):
        self.game_repository.set_round_mapping(room_id, round_mapping)



        
        





       
    
