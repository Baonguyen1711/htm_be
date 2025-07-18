from typing import Any, Dict, List, Optional
from fastapi import logger
from .base import RealTimeBaseRepository

class RealtimeQuestionRepository(RealTimeBaseRepository):
    def __init__(self):
        super().__init__()
    

    def set_questions(self, room_id, questions):
        self.set_to_path(f"{room_id}/questions", questions)
    
    def get_questions(self, room_id):
        return self.read_from_path(f"{room_id}/questions")
    
    def set_current_question(self, room_id, question):
        self.set_to_path(f"{room_id}/currentQuestions", question)
    
    def get_current_question(self, room_id):
        return self.read_from_path(f"{room_id}/currentQuestions")
    
    def set_answers(self, room_id, answers):
        self.set_to_path(f"{room_id}/answers", answers)
    
    def get_answers(self, room_id):
        return self.read_from_path(f"{room_id}/answers")
    
    def set_current_correct_answer(self, room_id: str, answer: str):
        self.set_to_path(f"{room_id}/current_correct_answer", answer)

    

    


    

    

    
    def set_player_answer_correct(self, room_id: str, correct_data: List[Dict[str, Any]]) -> None:
        self.set_to_path(f"{room_id}/player_answer_correct", correct_data)

    def get_player_answer_correct(self, room_id: str) -> List[Dict[str, Any]]:
        return self.read_from_path(f"{room_id}/player_answer_correct")



    
