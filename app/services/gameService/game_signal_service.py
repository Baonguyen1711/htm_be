import datetime
import secrets
from typing import List, Optional
from fastapi import Depends

from ...repositories.realtimedb.game_repository import GameRepository
from ...services.test_service import TestService
from ...services.gameService.game_data_service import GameDataService
# FIXED: Import from service_dependencies to break circular import
from ...dependencies.service_dependencies import get_game_repository, get_test_service, get_game_data_service
from ...util.scheduling import schedule_timer_multiplayer_game, scheduler, remove_all_jobs_for_room
from ...helper.global_variable import is_key_exist_in_dict, group_id_list
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameSignalService:
    def __init__(self, game_repository: GameRepository = Depends(get_game_repository), test_service: TestService =Depends(get_test_service), game_data_service: GameDataService = Depends(get_game_data_service)):
        self.game_repository = game_repository
        self.test_service = test_service
        self.game_data_service = game_data_service

    def set_next_round(self, room_id: str, round_number: str) -> None:
        self.game_repository.set_next_round(room_id, round_number)

    def set_round_start(self, room_id: str, round_number: str) -> None:
        self.game_repository.set_round_start(room_id, round_number)

    def set_return_to_topic_selection(self, room_id: str, should_return: bool) -> None:
        self.game_repository.set_return_to_topic_selection(room_id, should_return)
    
    def set_star(self, room_id: str, player_name: str) -> None:
        self.game_repository.set_star(room_id, player_name)

    def send_currrent_turn_to_player(self, stt:int, room_id:str):
        self.game_repository.send_currrent_turn_to_player( stt, room_id)
    
    def set_open_buzz(self, room_id: str) -> None:
        self.game_repository.set_open_buzz(room_id)

    def buzz_first(self, room_id: str, player_name: str):
        self.game_repository.buzz_first(room_id, player_name)

    def reset_buzz(self,room_id: str):
        self.game_repository.reset_buzz(room_id)

    def reset_star(self,room_id: str):
        self.game_repository.reset_star(room_id)

    def open_buzz(self, room_id: str):
        self.game_repository.open_buzz(room_id)

    def close_buzz(self, room_id: str):
        self.game_repository.close_buzz(room_id)

    def set_start_time(self, room_id) -> None:
        self.game_repository.start_time(room_id)

    def show_rules(self, room_id: str, round_number: str):
        self.game_repository.show_rules(room_id, round_number)

    def hide_rules(self, room_id: str):
        self.game_repository.hide_rules(room_id)

    def play_media(self, room_id: str):
        self.game_repository.play_media(room_id)

    def stop_media(self, room_id: str):
        self.game_repository.stop_media(room_id)

    def send_group_invite_to_player(self, uid: str, room_id: str, target_player_uid: str, player_name: str, group_id: Optional[str] = None):

        random_key = secrets.token_hex(16)
        if group_id is None:
            group_id = random_key
        self.game_repository.send_group_invite_to_player(uid, room_id, group_id, target_player_uid, player_name)

    def send_question_job(self, uid, test_name, room_id, q_index):
        from ...dependencies.router_dependencies import get_game_data_service
        service = get_game_data_service()
        service.send_specific_question_to_player(uid, test_name, room_id, "multiplayer", None, None, q_index, None, None)

    def send_answer_to_player(self, room_id: str):
        from ...dependencies.router_dependencies import get_game_data_service
        service = get_game_data_service()
        service.send_answer_to_player(room_id)

    def trigger_scoreboard(self, room_id: str, question_number: int):
        from ...dependencies.router_dependencies import get_game_data_service
        service = get_game_data_service()
        service.trigger_scoreboard(room_id, question_number)

    def schedule_timer_multiplayer_game(self, uid: str, room_id: str, test_id: str, current_question_number: Optional[int] = None):
        total_question = self.test_service.get_total_question_by_test_id(test_id)
        test_name = self.test_service.get_test_name_by_test_id(test_id)
        logger.info(f"total_question {total_question}")
        # schedule = []

        base_time = int(datetime.datetime.now(tz=datetime.UTC).timestamp() * 1000)

        # offset before the first countdown starts (e.g., 10 seconds)
        initial_delay = 5000  
        # countdown duration before each question (3..2..1 etc.)
        countdown_duration = 3000
        # buffer between countdown and start (e.g., 2s to settle animations)
        settle_duration = 2000  
        # duration of a question
        question_duration = 15000  
        # buffer between questions (if you want a short gap)
        gap_between_questions = 500
        trigger_scoreboard_waiting_time = 1500  # time to wait before showing scoreboard
        current_offset = initial_delay

        start_index = current_question_number if current_question_number is not None else 0
        is_resume = True if current_question_number is not None else False
        logger.info(f"is resume {is_resume}")

        for i in range(0, total_question-start_index):
            count_down_time = base_time + initial_delay + i*(countdown_duration + settle_duration + question_duration + trigger_scoreboard_waiting_time + gap_between_questions)
            start_time = count_down_time + countdown_duration + settle_duration
            show_question_time = count_down_time + countdown_duration
            end_time = start_time + question_duration
            trigger_scoreboard_time = end_time + trigger_scoreboard_waiting_time

            logger.info(f"Scheduling Q{i+1}: countdown at {count_down_time}, start at {start_time}, reveal at {show_question_time}, end at {end_time}")

            #send countdown time for each question
            schedule_timer_multiplayer_game(
                room_id= room_id,
                trigger_time=count_down_time,
                question_number=i+1,
                trigger_function=self.game_repository.send_countdown_time,
                args=[room_id, count_down_time // 1000],
            )

            #show question after countdown
            schedule_timer_multiplayer_game(
                room_id=room_id,
                trigger_time=show_question_time,
                question_number=i+1,
                trigger_function=self.send_question_job,
                args=[uid, test_name, room_id,i+1 if current_question_number is None else current_question_number],
            )

            #send start time signal
            schedule_timer_multiplayer_game(
                room_id=room_id,
                trigger_time=start_time,
                question_number=i+1,
                trigger_function=self.set_start_time,
                args=[room_id],
            )

            #show answer after time end
            schedule_timer_multiplayer_game(
                room_id=room_id,
                trigger_time=end_time,
                question_number=i+1,
                trigger_function=self.send_answer_to_player,
                args=[room_id],
            )

            #show scoreboard after time end + waiting time
            schedule_timer_multiplayer_game(
                room_id=room_id,
                trigger_time=trigger_scoreboard_time,
                question_number=i+1,
                trigger_function=self.trigger_scoreboard,
                args=[room_id, i + 1],
            )

            if(i+1 == total_question):
                # End game after the last question's scoreboard
                schedule_timer_multiplayer_game(
                    room_id=room_id,
                    trigger_time=trigger_scoreboard_time + 5000,  # 5 seconds after last scoreboard
                    question_number=i+1,
                    trigger_function=self.end_multiplayer_game,
                    args=[room_id],
                )

            # schedule.append({
            #     "questionNumber": i + 1,
            #     "countDownTime": count_down_time,
            #     "revealTime": show_question_time,
            #     "startTime": start_time,
            #     "endTime": end_time
            # })

            # schedule_timer_multiplayer_game(room_id, end_time, i, test_id)

            # # prepare offset for the next question
            # current_offset = end_time - base_time + gap_between_questions
            # logger.info(f"current_offset {current_offset}")
            # logger.info(f"schedule {schedule}")


        group_id_list_from_db = self.game_repository.find_objects_with_field(f"rooms/{room_id}/scores", "groupId")
        logger.info(f"group_id_list_from_db: {group_id_list_from_db}")
        is_rooms_in_global = is_key_exist_in_dict(room_id, group_id_list)
        if not is_rooms_in_global:
            group_id_list[room_id] = []

            for key, value in group_id_list_from_db.items():
                group_id = value.get("groupId")
                uid_list = value.get("uid", [])
                group_id_list[room_id].append({
                    f"{group_id}": uid_list
                })

            logger.info(f"group_id_list after adding: {group_id_list}")

        
        # logger.info(f"schedule after {schedule}")
        # self.game_repository.schedule_timer_multiplayer_game(room_id, schedule, is_resume)

    def pause_timer_multiplayer_game(self, room_id: str):
        remove_all_jobs_for_room(room_id)
        self.game_repository.pause_timer_multiplayer_game(room_id)

    def end_multiplayer_game(self, room_id: str):
        self.game_repository.end_multiplayer_game(room_id)

    def set_player_color(self, room_id: str, player_stt: str, color: str):
        logger.info(f"set_player_color {color}")
        logger.info(f"set_player_color {room_id}")
        self.game_repository.set_player_color(room_id, player_stt, color)

    def remove_player_color(self, room_id: str, player_stt: str):
        """Remove color for a specific player in Round 4"""
        self.game_repository.remove_player_color(room_id, player_stt)
    