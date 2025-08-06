from typing import List
from pydantic import BaseModel
from .scores import Score

class History(BaseModel):
    class Config:
        extra = "allow"  # Allow extra fields not defined in the model

    # Define fields as optional; add more as needed
    uid: str | None = None  # User ID field
    room_id: str | None = None
    test_name: str | None = None
    created_at: str | None = None  # Timestamp when history was created
    round_1: List[Score] | None = None
    round_2: List[Score] | None = None
    round_3: List[Score] | None = None
    round_4: List[Score] | None = None
