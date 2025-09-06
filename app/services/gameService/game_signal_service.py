from typing import List, Optional
from fastapi import Depends
from ...repositories.realtimedb.game_repository import GameRepository
from ...services.test_service import TestService
# FIXED: Import from service_dependencies to break circular import
from ...dependencies.service_dependencies import get_game_repository, get_test_service
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameSignalService:
    def __init__(self, game_repository: GameRepository = Depends(get_game_repository), test_service: TestService =Depends(get_test_service)):
        self.game_repository = game_repository
        self.test_service = test_service

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

    def set_player_color(self, room_id: str, player_stt: str, color: str):
        logger.info(f"set_player_color {color}")
        logger.info(f"set_player_color {room_id}")
        self.game_repository.set_player_color(room_id, player_stt, color)

    def remove_player_color(self, room_id: str, player_stt: str):
        """Remove color for a specific player in Round 4"""
        self.game_repository.remove_player_color(room_id, player_stt)
    