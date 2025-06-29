from typing import List
from pydantic import BaseModel

class Score(BaseModel):
    class Config:
        extra = "allow"  # Allow extra fields not defined in the model

    # Define fields as optional; add more as needed
    playerName: str | None = None
    avatar: str | None = None 
    score: int | None = None
    isCorrect: bool | None = None
    isModified: bool | None = None
    stt: str | None = None

class ScoreRule(BaseModel):
    round1: List[int]
    round2: List[int]
    round3: int

    class Config:
        extra = "allow"  # Allow extra fields not defined in the model


