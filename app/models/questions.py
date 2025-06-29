from decimal import Decimal
from pydantic import BaseModel
from typing import List

class UpdateQuestionRequest(BaseModel):
    class Config:
        extra = "allow"  # Allow extra fields not defined in the model

    # Define fields as optional; add more as needed
    question: str | None = None
    answer: str | None = None
    type: str | None = None
    imgUrl: str | None = None
    round:int | None = None
    test_id: str | None = None

class Answer(BaseModel):
    answer: str
    player_name: str | None = None
    avatar: str | None = None
    row: str | None = None
    is_obstacle: bool | None = None
    uid: str | None = None
    stt: str | None = None
    time: Decimal | None = None


class Grid(BaseModel):
    grid: List[List[str]]

class PlacementArray(BaseModel):
    row_index: int
    col_index: int
    index: int
    is_row: bool
    word: str