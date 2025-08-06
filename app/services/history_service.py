from fastapi import Depends

from ..models.history import History
from ..repositories.firestore.history_repository import HistoryRepository 
# FIXED: Import from service_dependencies instead of router_dependencies to break circular import
from ..dependencies.service_dependencies import get_history_repository
from ..repositories.realtimedb.game_repository import GameRepository
from ..dependencies.service_dependencies import get_game_repository


import logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoryService:
    def __init__(self, history_repository: HistoryRepository, game_repository: GameRepository = None):
        self.history_repository = history_repository
        self.game_repository = game_repository or get_game_repository()

    def update_match_history(self, room_id: str, uid: str):
        logger.info("Attempting to create reference to Firebase")
        data = self.game_repository.get_round_scores(room_id)
        logger.info(f"round_scores {data}")

        # Handle the list structure from Firebase
        if isinstance(data, list):
            # Convert list structure to flat dict format with rounds at top level
            data_dict = {}
            for round_index, round_data in enumerate(data):
                if round_index == 0:
                    continue  # Skip index 0 which is None
                if round_data and isinstance(round_data, list):
                    # Filter out None values and create clean player list
                    players = [player for player in round_data if player is not None]
                    data_dict[f"round_{round_index}"] = players
        elif isinstance(data, dict):
            # If data is already a dict, use it as is
            data_dict = data
        else:
            # If data is None or other type, create empty dict
            data_dict = {}

        # Try to get the test name (selected packet) from the room
        try:
            test_name = self.game_repository.read_from_path(f"{room_id}/selectedPacket")
            if test_name:
                data_dict["test_name"] = test_name
                logger.info(f"Added test_name: {test_name}")
        except Exception as e:
            logger.warning(f"Could not retrieve test_name: {str(e)}")

        # Add room_id to the data
        data_with_room = {**data_dict, "room_id": room_id}
        document_id = self.history_repository.create_history(uid, data_with_room)
        logger.info(f"Created new history entry with ID: {document_id}")
        logger.info(f"updated_data {data_with_room}")

    def get_history_by_user_id(self, uid: str):
        logger.info("Attempting to retrieve history from Firebase")
        history_list = self.history_repository.get_history_by_user_id(uid)
        logger.info(f"Found {len(history_list) if history_list else 0} history entries for user {uid}")
        logger.info(f"history {history_list}")
        return history_list