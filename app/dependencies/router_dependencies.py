from ..database import db 
from dotenv import load_dotenv
from functools import lru_cache

from app.services.s3_service import S3Service
from app.services.sound_service import SoundService
from app.services.test_service import TestService
from app.services.auth_service import AuthService
from app.services.history_service import HistoryService
from app.services.room_service import RoomService
from app.services.gameService.game_data_service import GameDataService
from app.services.gameService.game_signal_service import GameSignalService


# FIXED: Import service factories from service_dependencies to break circular imports
from .service_dependencies import (
    get_game_repository, get_history_repository, get_question_repository,
    get_realtime_db, get_realtime_question_repository, get_room_repository,
    get_test_repository, get_user_repository, get_test_service
)
import firebase_admin
from firebase_admin import auth, credentials

import os
import logging

load_dotenv()

# Cache Firebase Realtime Database
@lru_cache
def get_db():
    return db

# Service factories - now using the ones from service_dependencies to avoid circular imports
# get_test_service is imported from service_dependencies above

@lru_cache
def get_game_data_service():
    return GameDataService(get_game_repository(), get_test_service())

@lru_cache
def get_game_signal_service():
    return GameSignalService(get_game_repository(), get_test_service())

@lru_cache
def get_s3_service():
    return S3Service()

@lru_cache
def get_sound_service():
    return SoundService()

@lru_cache
def get_auth_service():
    return AuthService(get_room_repository(), get_user_repository())

@lru_cache
def get_history_service():
    return HistoryService(get_history_repository())

@lru_cache
def get_room_service():
    return RoomService(get_room_repository(), get_game_repository())