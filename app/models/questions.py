from pydantic import BaseModel

class UpdateQuestionRequest(BaseModel):
    class Config:
        extra = "allow"  # Allow extra fields not defined in the model

    # Define fields as optional; add more as needed
    question: str | None = None
    answer: str | None = None
    type: str | None = None
    imgUrl: str | None = None

class Answer(BaseModel):
    answer: str