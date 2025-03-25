from pydantic import BaseModel

class User(BaseModel):
    stt: str
    userName: str
    avatar: str

