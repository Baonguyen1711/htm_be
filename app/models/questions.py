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
    round: str | None = None
    test_id: str | None = None

class Answer(BaseModel):
    answer: str
    row: str | None = None
    is_obstacle: bool | None = None
    uid: str | None = None
    stt: str | None = None


class Grid(BaseModel):
    grid: List[List[str]]
