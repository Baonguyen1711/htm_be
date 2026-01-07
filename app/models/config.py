from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel

class RoundType(str, Enum):
    SIMPLE_QUESTION = "simple_question"
    OBSTACLE = "obstacle"
    PACKET = "packet"
    




class Question(BaseModel):
    id: str
    content: str
    override: dict = {}


class RoundCreate(BaseModel):
    type: RoundType
    config: dict           # default
    questions: list[Question]



class MatchCreate(BaseModel):
    rounds: List[RoundCreate]
