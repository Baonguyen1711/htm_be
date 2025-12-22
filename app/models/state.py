from typing import List
from pydantic import BaseModel

class GameState(BaseModel):
    phase: str | None = None
    phaseId: str | None = None
    test_name: str | None = None
    currentQuestion: int | None = None
    phaseStartTime: int | None = None
    phaseDuration: int | None = None
    endedAt: int | None = None
    ended: bool | None = None
