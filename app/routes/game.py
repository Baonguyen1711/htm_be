import asyncio
import json
import logging
import traceback
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException, Request
from firebase_admin import db

from ..models.scores import Score, ScoreRule
from ..util.string_processing import normalize_string

from ..models.questions import Answer, Grid
from ..models.state import GameState
from ..services.gameService.game_data_service import GameDataService
from ..services.gameService.game_signal_service import GameSignalService
from ..services.test_service import TestService
from ..helper.exception import handle_exceptions
from ..helper.host_only import host_only
from ..dependencies.router_dependencies import get_game_data_service, get_game_signal_service, get_test_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameRouter:
    def __init__(self, game_data_service: GameDataService = None, game_signal_service: GameSignalService = None, test_service: TestService = None):

        self.game_data_service = game_data_service or get_game_data_service()
        self.game_signal_service = game_signal_service or get_game_signal_service()
        self.test_service = test_service or get_test_service()
        self.router = APIRouter(prefix="/api/game")


        self.router.get("/question/round")(self.get_each_round_questions)
        self.router.get("/question/prefetch")(self.prefetch_question)
        self.router.get("/question/round/packet")(self.get_packets_name)
        self.router.get("/question/next")(self.send_next_question_to_player)
        self.router.get("/question")(self.send_specific_question)

        self.router.post("/round/mapping")(self.set_round_mapping)
        self.router.post("/grid/cell")(self.set_selected_cell)
        self.router.post("/grid/color")(self.set_cell_color)
        self.router.post("/grid")(self.send_grid_to_player)
        self.router.post("/row/action")(self.set_row_action)
        self.router.post("/obstacle")(self.open_obstacle)
        self.router.post("/packet/set")(self.set_selected_packet_name)
        self.router.post("/packet/used")(self.set_used_packet_name)
        self.router.post("/packet/return")(self.set_return_to_packet_selection)
        self.router.post("/answer")(self.send_answer)
        self.router.post("/round/start")(self.send_start_round_signal)
        self.router.post("/time")(self.send_start_time_signal)
        self.router.post("/turn")(self.update_turn)
        self.router.post("/player/color")(self.set_player_color)
        self.router.post("/score/rules")(self.apply_score_rule)
        self.router.post("/score")(self.scoring)
        self.router.post("/broadcast")(self.broadcast_answer)
        self.router.post("/rules/hide")(self.hide_room_rules)
        self.router.post("/rules/show")(self.show_room_rules)
        self.router.post("/media/start")(self.play_media)
        self.router.post("/media/stop")(self.stop_media)

        self.router.post("/state/update")(self.update_game_state)

        #for player
        self.router.post("/submit")(self.submit_answer)

        #multiplayer mode
        self.router.post("/multiplayer/submit")(self.submit_multiplayer_answer)
        self.router.post("/multiplayer/invite/accept")(self.join_group_invite)
        self.router.post("/multiplayer/invite")(self.send_group_invite)

        self.router.post("/multiplayer/start")(self.send_start_multiplayer_game_signal)
        self.router.post("/multiplayer/resume")(self.resume_multiplayer_game)
        self.router.post("/multiplayer/pause")(self.pause_multiplayer_game)
        self.router.post("/multiplayer/end")(self.end_multiplayer_game)

    
    @handle_exceptions
    @host_only
    def set_round_mapping(self, request: Request, room_id: str, round_mapping: List[int] = Body(...)):
        logger.info(f"round_mapping {round_mapping}")

        self.game_data_service.set_round_mapping(room_id, round_mapping)

        return {
            "message": f"add round mapping for room {room_id} successfully"
        }

    @handle_exceptions
    @host_only
    def set_selected_cell(self, request: Request,room_id: str,row_index:str, col_index:str):
        self.game_data_service.send_selected_cell(room_id,row_index, col_index)


    @handle_exceptions
    @host_only
    def set_cell_color(self, request: Request, room_id: str,row_index:str, col_index:str,color: str):
        self.game_data_service.send_cell_color(room_id,row_index,col_index,color)

    @handle_exceptions
    @host_only
    def send_grid_to_player(self, request: Request, room_id: str, grid: Grid, marked_characters_index: Optional[str] = None):
        self.game_data_service.send_grid(room_id, grid.grid, marked_characters_index)

    @handle_exceptions
    @host_only
    def set_row_action(self, request: Request, room_id: str, row_number: str, action:str, word_length: int,selected_row_index: int, selected_col_index: int, correct_answer: Optional[str] = None ,marked_characters_index: Optional[str] = None, is_row:Optional[bool] = None):
        if action == "SELECT":
            logger.info("Attempting to send selected row")
            self.game_data_service.send_selected_row(room_id, row_number,is_row, word_length,selected_row_index, selected_col_index)
        if action == "CORRECT":
            logger.info(f"marked_character_index {marked_characters_index}")
            self.game_data_service.send_correct_row(room_id, row_number, correct_answer, marked_characters_index, is_row,selected_row_index, selected_col_index)
        if action == "INCORRECT":
            logger.info("Attempting to send incorrect row")
            self.game_data_service.send_incorrect_row_to_player(room_id, row_number, is_row,word_length,selected_row_index, selected_col_index)

       
        
    @handle_exceptions
    @host_only
    async def open_obstacle(self, request: Request, room_id: str, grid: Grid):

        self.game_data_service.send_obstacle(room_id, grid)
        logger.info("obstacle opened")


    @handle_exceptions
    @host_only    
    def set_selected_packet_name(self, request: Request, packet_name: str,room_id:str):
        self.game_data_service.send_selected_packet_name_to_player(packet_name,room_id)

    @handle_exceptions
    @host_only    
    def set_used_packet_name(self, request: Request, room_id:str,used_packets: List[str] = Body(...)):
        self.game_data_service.send_used_packet_name_to_player(used_packets,room_id)

    @handle_exceptions
    @host_only    
    def set_return_to_packet_selection(self, request: Request, should_return: bool,room_id:str):
        self.game_data_service.send_should_return_to_packet_selection(should_return,room_id)


    @handle_exceptions
    @host_only
    def get_packets_name(self, request: Request, test_name:str ,room_id:str):

        user = request.state.user
        authenticated_uid = user["uid"]
        test_data = self.test_service.process_test_data(authenticated_uid, test_name)

        logger.info("Attempting to send packet name to player ")
        packets = self.test_service.get_packet_name(test_data)
        self.game_data_service.send_packet_name_to_player(packets,room_id)
        return packets
                
    @handle_exceptions
    @host_only
    def get_each_round_questions(self, request: Request, test_name:str, round: str, packet_name: Optional[str] = None, difficulty: Optional[str] = None):

        user = request.state.user
        authenticated_uid = user["uid"]
        test_data = self.test_service.process_test_data(authenticated_uid, test_name)

        logger.info("Attempting to get question by round")
        questions = self.test_service.get_questions_by_round(test_data,round,packet_name, difficulty)

        return questions

    @handle_exceptions
    @host_only
    def prefetch_question(self, request: Request, test_name:str, round: str, packet_name: Optional[str] = None, difficulty: Optional[str] = None, question_number: Optional[int] | None= None):

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
    
    def send_packets_name(self, request: Request, room_id: str, test_name: str):
        self.game_data_service.send_packet_name_to_player



    @handle_exceptions
    @host_only
    def send_specific_question(self, request: Request, test_name:str, round: str, room_id: str, packet_name: Optional[str] = None, difficulty: Optional[str] = None, question_number: Optional[int] | None= None, page: Optional[int] | None = None, limit: Optional[int] | None = None):
        user = request.state.user
        authenticated_uid = user["uid"]
        logger.info(f"Requesting question for room {room_id}, round {round}, packet {packet_name}, difficulty {difficulty}, question_number {question_number}, page {page}, limit {limit}")
        #self.game_data_service.reset_player_answer(room_id)
        question = self.game_data_service.send_specific_question_to_player(authenticated_uid, test_name, room_id, round, packet_name, difficulty, question_number, page, limit)
        logger.info(f"Question sent to room {room_id}: {question}")
        return question
    
    @handle_exceptions
    @host_only
    def send_next_question_to_player(self, request: Request, test_name:str, round: str, room_id: str, packet_name: Optional[str] = None, difficulty: Optional[str] = None, question_number: Optional[int] | None= None, page: Optional[int] | None = None, limit: Optional[int] | None = None):
        user = request.state.user
        authenticated_uid = user["uid"]
        logger.info(f"Requesting question for room {room_id}, round {round}, packet {packet_name}, difficulty {difficulty}, question_number {question_number}, page {page}, limit {limit}")
        #self.game_data_service.reset_player_answer(room_id)
        self.game_data_service.get_next_question(authenticated_uid, test_name, room_id, round, packet_name, difficulty, question_number, page, limit)
        #logger.info(f"Question sent to room {room_id}: {question}")
        return {
            "message": "send next question successfully"
        }

    @handle_exceptions
    @host_only                    
    def send_answer(self, request: Request, room_id: str):
        logger.info("Attempting to send answer to player")
        self.game_data_service.send_answer_to_player(room_id)
        logger.info("answer sent!")


    @handle_exceptions
    @host_only
    def send_start_time_signal(self, request: Request, room_id: str, time_duration: Optional[int] = None):
        logger.info("Attempting to start time")
        self.game_signal_service.set_start_time(room_id, time_duration)
        logger.info("time started")
    
    @handle_exceptions
    @host_only
    def send_start_round_signal(self, request: Request, room_id: str, round: str) -> None:
        self.game_signal_service.set_round_start(room_id, round)
    
    @handle_exceptions
    def submit_answer(self, request: Request, room_id: str, answer: Answer):
        user = request.state.user
        authenticated_uid = user["uid"]
        self.game_data_service.submit_answer(room_id, authenticated_uid, answer)
        
    
    @handle_exceptions
    @host_only
    def apply_score_rule(self, request: Request,room_id: str, score_rules: ScoreRule):
        self.game_data_service.set_score_rules(room_id, score_rules)
        
    
    @handle_exceptions
    @host_only
    def scoring(
            self, request: Request,
            room_id: str, 
            mode: str,
            round: Optional[str] = None, 
            stt: Optional[str] = None,
            is_obstacle_correct: Optional[str] = None,
            obstacle_point: Optional[int] = None,
            is_correct: Optional[str] = None,
            round_4_mode: Optional[str] = None,
            difficulty: Optional[str] = None,
            is_take_turn_correct: Optional[str] = None,
            stt_take_turn: Optional[str] = None,
            stt_taken: Optional[str] = None,
            scores: Optional[List[Score]] = Body(...), 
        ):
        score_list = self.game_data_service.score(
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

        return score_list
        
    
    @handle_exceptions
    @host_only
    def broadcast_answer(self, request: Request,room_id: str):
        player_answer = self.game_data_service.get_all_player_answer(room_id)
        logger.info(f"player_answer {player_answer}")
        self.game_data_service.broadcast_player_answer(room_id,list(player_answer.values()))    
        return list(player_answer.values())
    
    @handle_exceptions
    @host_only
    def update_turn(self, request: Request, turn: int, room_id: str):
        self.game_signal_service.send_currrent_turn_to_player(turn,room_id)
        return {"message": "set current turn sucessfully", "stt": turn}

    @handle_exceptions
    @host_only
    def set_player_color(self, request: Request, room_id: str, player_stt: str, request_body: dict = Body(...)):
        """Set color for a specific player in Round 4"""
        color = request_body.get("color", "")
        logger.info(f"set_player_color {color}")
        if color and color.strip():
            self.game_signal_service.set_player_color(room_id, player_stt, color)
            return {"data": {"success": True}, "message": f"Color set successfully for player {player_stt}"}
        else:
            # Remove color if empty
            self.game_signal_service.remove_player_color(room_id, player_stt)
            return {"data": {"success": True}, "message": f"Color removed for player {player_stt}"}
      
    @handle_exceptions
    @host_only
    def show_room_rules(self, request: Request, room_id: str, round_number: str):
        self.game_signal_service.show_rules(room_id, round_number)
        return {"message": "Rules shown successfully", "room_id": room_id, "round": round_number}


    @handle_exceptions
    @host_only
    def hide_room_rules(self, request: Request, room_id: str):
        self.game_signal_service.hide_rules(room_id)
        return {"message": "Rules hidden successfully", "room_id": room_id}
    
    @handle_exceptions
    @host_only
    def play_media(self, request: Request,room_id: str):
        self.game_signal_service.play_media(room_id)

    @handle_exceptions
    @host_only
    def stop_media(self, request: Request, room_id: str):
        self.game_signal_service.stop_media(room_id)

    @handle_exceptions
    async def send_start_multiplayer_game_signal(self, request: Request, room_id: str, test_name: str, play_mode: str):
        user = request.state.user
        authenticated_uid = user["uid"]
        logger.info(f"start multiplayer game")
        if play_mode == "auto":
            asyncio.create_task(
                self.game_signal_service.schedule_timer_multiplayer_game(
                    room_id,
                    authenticated_uid,
                    test_name
                )
            )

        if play_mode == "manual":
            self.game_data_service.update_game_state(room_id, 
                state= {
                    "phase": "COUNTDOWN"
                }
            )

        return {
            "status": "started",
            "roomId": room_id
        }
    
    @handle_exceptions
    @host_only
    def update_game_state(self, request: Request, room_id: str, state: Dict[str, Any] = Body(...)):
        
        self.game_data_service.update_game_state(room_id, state)


    @handle_exceptions
    @host_only
    def pause_multiplayer_game(self, request: Request, room_id: str):
        self.game_signal_service.pause_timer_multiplayer_game(room_id)

    @handle_exceptions
    @host_only
    async def resume_multiplayer_game(self, request: Request, room_id: str, test_name: str):
        user = request.state.user
        authenticated_uid = user["uid"]

        asyncio.create_task(
        self.game_signal_service.resume_game(room_id, authenticated_uid, test_name)
        )
        return {
            "status": "resume"
        }

    @handle_exceptions
    def submit_multiplayer_answer(self, request: Request, room_id: str, answer: Answer, test_name: str, group_id: Optional[str] = None):
        user = request.state.user
        authenticated_uid = user["uid"]
        self.game_data_service.multiplayer_submit_answer(room_id, authenticated_uid, answer, test_name, group_id)
        return {"message": "Answer submitted successfully"}
    
    @handle_exceptions
    @host_only
    def end_multiplayer_game(self, request: Request, room_id: str):
        self.game_signal_service.end_multiplayer_game(room_id)

    @handle_exceptions
    def send_group_invite(self, request: Request, room_id: str, target_player_uid: str, player_name: str, group_id: Optional[str] = None):
        user = request.state.user
        authenticated_uid = user["uid"]
        self.game_signal_service.send_group_invite_to_player(authenticated_uid, room_id, target_player_uid, player_name, group_id)
        return {"message": "Group invite sent successfully"}
    
    @handle_exceptions
    def join_group_invite(self, request: Request, room_id: str, group_id: str, inviter_uid: str):
        user = request.state.user
        authenticated_uid = user["uid"]
        self.game_data_service.join_group_invite(room_id, group_id, authenticated_uid, inviter_uid)
        return {"message": "Joined group invite successfully"}
    
    # @handle_exceptions
    # def accept_group_invite(self, request: Request, room_id: str, group_id: str):
    #     user = request.state.user
    #     authenticated_uid = user["uid"]
    #     self.game_data_service.accept_group_invite(room_id, authenticated_uid, group_id)
    #     return {"message": "Accepted group invite successfully"}

    
    # @handle_exceptions
    # @host_only
    # def create_practice_room(self, request: Request, room_id: str, room_data: Dict[str, str]):
    #     user = request.state.user
    #     authenticated_uid = user["uid"]
    #     email = user.get("email", "")
    #     if not email or "@" not in email:
    #         raise ValueError("Only hosts with valid email can create practice rooms")
        
    #     self.game_data_service.create_practice_room(room_id, room_data)
    #     return {"message": "Practice room created successfully", "roomId": room_id}    

    



      
