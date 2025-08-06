from pydantic import BaseModel

class User(BaseModel):
    uid: str | None = None
    stt: str
    userName: str
    avatar: str



