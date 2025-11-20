from ..database import db 
from dotenv import load_dotenv
from functools import lru_cache

from app.repositories.firestore.test_repository import TestRepository
from app.repositories.firestore.room_repository import RoomRepository
from app.repositories.firestore.question_repository import QuestionRepository
from app.repositories.firestore.user_repository import UserRepository
from app.repositories.firestore.history_repository import HistoryRepository
from app.repositories.realtimedb.game_repository import GameRepository
from app.repositories.realtimedb.realtime_question_repository import RealtimeQuestionRepository
import firebase_admin
from firebase_admin import auth, credentials

import os
import logging

load_dotenv()

# Initialize repositories (cached)
# FIXED: Pass database instance directly to break circular import
@lru_cache
def get_test_repository():
    return TestRepository(db)

@lru_cache
def get_room_repository():
    return RoomRepository(db)

@lru_cache
def get_game_repository():
    return GameRepository()  # This one doesn't inherit from BaseRepository

@lru_cache
def get_question_repository():
    return QuestionRepository(db)

@lru_cache
def get_realtime_question_repository():
    return RealtimeQuestionRepository()  # This one doesn't inherit from BaseRepository

@lru_cache
def get_user_repository():
    return UserRepository(db)

@lru_cache
def get_history_repository():
    return HistoryRepository(db)

# Add missing function for realtime database
@lru_cache
def get_realtime_db():
    return db  # Return the same database instance

# Service factories (moved from router_dependencies to break circular imports)
@lru_cache
def get_test_service():
    from app.services.test_service import TestService
    return TestService(
        get_test_repository(),
        get_question_repository(),
        get_realtime_question_repository()
    )

@lru_cache
def get_game_data_service():
    from app.services.gameService.game_data_service import GameDataService
    return GameDataService(
        get_game_repository(),
        get_test_service()
    )
