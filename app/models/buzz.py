from pydantic import BaseModel

class BuzzRequest(BaseModel):
    uid: str | None = None
    stt: str | None = None
    player_name: str | None = None