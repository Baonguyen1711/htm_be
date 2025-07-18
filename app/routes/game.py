import logging
import traceback
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, logger
from firebase_admin import db

from ..models.scores import Score, ScoreRule
from ..util.string_processing import normalize_string

from ..models.questions import Answer, Grid
from ..services.gameService.game_data_service import GameDataService
from ..services.gameService.game_signal_service import GameSignalService
from ..services.test_service import TestService
from ..helper.exception import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameRouter:
    def __init__(self,game_data_service: GameDataService, game_signal_service: GameSignalService, test_service: TestService):
        self.game_data_service = game_data_service
        self.game_signal_service = game_signal_service
        self.test_service = test_service
        self.router = APIRouter(prefix="/api/game")


        self.router.get("/question/round")(self.get_each_round_questions)
        self.router.get("/question/prefetch")(self.prefetch_question)
        self.router.get("/question/round/packet")(self.get_packets_name)
        self.router.get("/question")(self.send_specific_question)

        self.router.post("/grid/cell")(self.set_selected_cell)
        self.router.post("/grid/color")(self.set_cell_color)
        self.router.post("/grid")(self.send_grid_to_player)
        self.router.post("/row/action")(self.set_row_action)
        self.router.post("/obstacle")(self.open_obstacle)
        self.router.post("/packet/set")(self.set_selected_packet_name)
        self.router.post("/answer")(self.send_answer)
        self.router.post("/round/start")(self.send_start_round_signal)
        self.router.post("/time")(self.send_start_time_signal)
        self.router.post("/submit")(self.submit_answer)
        self.router.post("/turn")(self.update_turn)
        self.router.post("/score/rules")(self.apply_score_rule)
        self.router.post("/score")(self.scoring)
        self.router.post("/broadcast")(self.broadcast_answer)
        self.router.post("/rules/hide")(self.hide_room_rules)
        self.router.post("/rules/show")(self.show_room_rules)

    
    @handle_exceptions
    def set_selected_cell(self,room_id: str,row_index:str, col_index:str):
        self.game_data_service.send_selected_cell(room_id,row_index, col_index)


    @handle_exceptions
    def set_cell_color(self, room_id: str,row_index:str, col_index:str,color: str):

        self.game_data_service.send_cell_color(room_id,row_index,col_index,color)



    @handle_exceptions
    def send_grid_to_player(self, room_id: str, grid: Grid):
        self.game_data_service.send_grid(room_id, grid.grid)

        

    @handle_exceptions
    def set_row_action(self, room_id: str, row_number: str, action:str, word_length: int,correct_answer: Optional[str] = None ,marked_characters_index: Optional[str] = None, is_row:Optional[bool] = None):
        if action == "SELECT":
            logger.info("Attempting to send selected row")
            self.game_data_service.send_selected_row(room_id, row_number,is_row, word_length)
        if action == "CORRECT":
            logger.info(f"marked_character_index {marked_characters_index}")
            self.game_data_service.send_correct_row(room_id, row_number, correct_answer, marked_characters_index, is_row)
        if action == "INCORRECT":
            logger.info("Attempting to send incorrect row")
            self.game_data_service.send_incorrect_row_to_player(room_id, row_number, is_row,word_length)

       
        
    @handle_exceptions
    async def open_obstacle(self, room_id: str, obstacle: str ,request: Request):

        body = await request.json()
        logger.info(f"Received body: {body}")
    
        placementArray = body  
        self.game_data_service.send_obstacle(room_id, obstacle,placementArray)
        logger.info("obstacle opened")


    @handle_exceptions    
    def set_selected_packet_name(self, packet_name: str,room_id:str,request: Request):
        self.game_data_service.send_selected_packet_name_to_player(packet_name,room_id)


    @handle_exceptions
    def get_packets_name(self, test_name:str ,room_id:str,request: Request):

        user = request.state.user
        authenticated_uid = user["uid"]
        test_data = self.test_service.process_test_data(authenticated_uid, test_name)

        logger.info("Attempting to send packet name to player ")
        packets = self.test_service.get_packet_name(test_data)
        self.game_data_service.send_packet_name_to_player(packets,room_id)
        return packets
                
    @handle_exceptions
    def get_each_round_questions(self, test_name:str, round: str,request: Request, packet_name: Optional[str] = None, difficulty: Optional[str] = None):

        user = request.state.user
        authenticated_uid = user["uid"]
        test_data = self.test_service.process_test_data(authenticated_uid, test_name)

        logger.info("Attempting to get question by round")
        questions = self.test_service.get_questions_by_round(test_data,round,packet_name, difficulty)

        return questions

    @handle_exceptions
    def prefetch_question(self, test_name:str, round: str, request: Request, packet_name: Optional[str] = None, difficulty: Optional[str] = None, question_number: Optional[str] | None= None):

        user = request.state.user
        authenticated_uid = user["uid"]
        test_data = self.test_service.process_test_data(authenticated_uid, test_name)

        logger.info("Prefetching question for host preview")
        question_with_answer = self.test_service.get_specific_question(test_data, round, packet_name, difficulty, None, question_number)
        logger.info("Prefetch successful")
        
        return {
            "question": question_with_answer,
            "answer": question_with_answer.get("answer", ""),
            "prefetch": True
        }
    
    def send_packets_name(self, room_id: str, test_name: str):
        self.game_data_service.send_packet_name_to_player



    @handle_exceptions
    def send_specific_question(self, test_name:str, round: str, room_id: str,request: Request, packet_name: Optional[str] = None, difficulty: Optional[str] = None, question_number: Optional[str] | None= None, page: Optional[int] | None = None, limit: Optional[int] | None = None):
        user = request.state.user
        authenticated_uid = user["uid"]
        test_data = self.test_service.process_test_data(authenticated_uid, test_name)
        logger.info(f"test_data {test_data}")

        question = self.test_service.get_specific_question(test_data,round,packet_name, difficulty, question_number=question_number, page=page, limit=limit)
        question_without_answer = self.test_service.get_question_without_answer(question, room_id)
        self.game_data_service.send_question_to_player(room_id,question_without_answer)
        return question

    @handle_exceptions                    
    def send_answer(self, room_id: str,answer:Answer):
        logger.info("Attempting to send answer to player")
        self.game_data_service.send_answer_to_player(answer.answer,room_id)
        logger.info("answer sent!")


    @handle_exceptions
    def send_start_time_signal(self, room_id: str):
        logger.info("Attempting to start time")
        self.game_signal_service.set_start_time(room_id)
        logger.info("time started")
    
    @handle_exceptions
    def send_start_round_signal(self, room_id: str, round: str, grid: Grid = None) -> None:
        self.game_signal_service.set_round_start(room_id, round, grid.grid)
    
    @handle_exceptions
    def submit_answer(self, room_id: str, answer: Answer,request: Request):
        user = request.state.user
        authenticated_uid = user["uid"]
        self.game_data_service.submit_answer(room_id, authenticated_uid, answer)
        
    
    @handle_exceptions
    def apply_score_rule(self,room_id: str, rules: ScoreRule):
        self.game_data_service.set_score_rules(room_id, rules)
        
    
    @handle_exceptions
    def scoring(
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
        self.game_data_service.score(
            room_id, 
            mode,
            scores, 
            round, 
            stt,
            is_obstacle_correct,
            obstacle_point,
            is_correct,
            round_4_mode,
            difficulty,
            is_take_turn_correct,
            stt_take_turn,
            stt_taken
        )
        
    
    @handle_exceptions
    def broadcast_answer(self,room_id: str):
        player_answer = self.game_data_service.get_all_player_answer(room_id)
        logger.info(f"player_answer {player_answer}")
        self.game_data_service.broadcast_player_answer(room_id,list(player_answer.values()))    
        return list(player_answer.values())
    
    @handle_exceptions
    def update_turn(self, turn: int, room_id: str): 
        self.game_signal_service.send_currrent_turn_to_player(turn,room_id)
        return {"message": "set current turn sucessfully", "stt": turn}
      
    @handle_exceptions
    def show_room_rules(self, room_id: str, round_number: str):
        self.game_signal_service.show_rules(room_id, round_number)
        return {"message": "Rules shown successfully", "room_id": room_id, "round": round_number}


    @handle_exceptions
    def hide_room_rules(self, room_id: str):
        self.game_signal_service.hide_rules(room_id)
        return {"message": "Rules hidden successfully", "room_id": room_id}

      
