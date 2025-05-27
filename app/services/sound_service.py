import boto3
import uuid
from fastapi import UploadFile
from botocore.exceptions import ClientError
from typing import Dict, Optional
from io import BytesIO
import os
from dotenv import load_dotenv
import logging
import traceback
logging.basicConfig(level=logging.INFO)
from .realtime_service import play_sound
logger = logging.getLogger(__name__)

load_dotenv()


class SoundService:
    def __init__(self):
        pass

    def play_sound_by_round(self, room_id: str, type: str) -> str:
        play_sound(room_id, type)
        return f"Sound {type} played for room {room_id}"

   
    
