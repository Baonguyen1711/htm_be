from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict
from app.services.s3_service import S3Service
from app.services.firestore_service import save_file_key_for_user
from starlette.requests import Request
from app.services.sound_service import SoundService


class SoundRouter:
    def __init__(self, sound_service: SoundService):
        self.sound_service = sound_service
        self.router = APIRouter()

        self.router.post("/api/sound/play")(self.play_sound)

    def play_sound(self, room_id: str, type: str):
        try:
            result = self.sound_service.play_sound_by_round(room_id, type)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    