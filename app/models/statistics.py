from typing import List
from pydantic import BaseModel

class DetailStatistics(BaseModel):
    question: str
    answer: str
    correct_answer: str
    is_correct: bool

class Statistics(BaseModel):
    test_name: str
    statistic: List[DetailStatistics]

class UserStatistics(BaseModel):
    statistics: List[Statistics]
