# Process and cache test data

from collections import defaultdict
import logging
from fastapi import FastAPI, Depends, UploadFile

from app.services.firestore_service import upload_test_to_firestore, get_test_by_name, get_test_name_by_user_id, update_question, get_test_by_test_id
from .cache_service import get_cached_test, set_cached_test, clear_cached_test
from typing import Optional
from fastapi import HTTPException, status, Depends
from ..repositories.firestore.test_repository import TestRepository
from ..repositories.firestore.question_repository import QuestionRepository
from ..repositories.realtimedb.realtime_question_repository import RealtimeQuestionRepository
from ..util.file_processing import process_excel_file
from google.cloud import firestore
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestService:
    def __init__(self, test_repository: TestRepository, question_repository: QuestionRepository, realtime_question_repository: RealtimeQuestionRepository):
        self.test_repository = test_repository
        self.question_repository = question_repository
        self.realtime_question_repository = realtime_question_repository

    def get_test_name_by_user_id(self, uid: str):
        test_list = self.test_repository.get_tests_by_user_id(uid)
        logger.info(f"test_list {test_list}")
        test_name_list = [test.get("testName") for test in test_list if isinstance(test, dict) and "testName" in test]
        logger.info(f"test_name_list {test_name_list}")
        if "error" in test_list:
            raise HTTPException(status_code=500, detail=test_list["error"])
        if len(test_list) == 0:
            raise HTTPException(status_code=404, detail="no test found")
        
        return test_name_list


    def process_test_data(self, uid: str, test_name: str):

        cached_data = get_cached_test(uid, test_name)
        if cached_data:
            return cached_data
        questions = get_test_by_name(uid,test_name)[0]["questions"]

        logger.info(f"Processing test data for {test_name}")
        logger.info(f"test data {questions}")

        round_1 = sorted([q for q in questions if q["round"] == 1], key=lambda x: x["stt"])
        round_2 = sorted([q for q in questions if q["round"] == 2], key=lambda x: x["stt"])
        turn = sorted([q for q in questions if q["round"] == "turn"], key=lambda x: x["stt"])

        grouped_round_3 = defaultdict(list)
        for q in [q for q in questions if q["round"] == 3]:
            grouped_round_3[q["packetName"]].append(q)
        for packet_name in grouped_round_3:
            grouped_round_3[packet_name].sort(key=lambda x: x["stt"])

        grouped_round_4 = defaultdict(list)
        for q in [q for q in questions if q["round"] == 4]:
            grouped_round_4[q["difficulty"]].append(q)
        for difficulty in grouped_round_4:
            grouped_round_4[difficulty].sort(key=lambda x: x["stt"])

        result = {
            "round_1": round_1,
            "round_2": round_2,
            "round_3": dict(grouped_round_3),
            "round_4": dict(grouped_round_4),
            "turn": turn
        }
        logger.info(f"result {result}")
        set_cached_test(uid, test_name, result)
        return result
    
    
    def get_test_for_each_round(self, uid: str, test_name: str):
        logger.info(f"test {self.test_repository.get_test_by_name_and_user_id(test_name, uid)}")
        tests = self.test_repository.get_test_by_name_and_user_id(test_name, uid)
        logger.info(f"tests {tests}")
        result = []
        for test_data in tests:
            logging.info(f"test_data: {type (test_data)}")
            test_id = test_data["testId"]

            logging.info(f"test_id: {type (test_id)}")

            questions = self.question_repository.get_questions_by_test_id(test_id)
            logging.info(f"questions {questions}")
            if questions:
                # Convert QuerySnapshot to list of dictionaries
                question_list = [q for q in questions] if questions else []

                # Combine test and its questions into a plain dict
                result.append({
                    "test": test_data,
                    "questions": question_list
                })
        logging.info(f"result {result}")
        question_list = result[0]["questions"]

        grouped_round_3 = defaultdict(list)
        grouped_round_4 = defaultdict(list)

        for question in [question for question in question_list if question["round"] == 3]:
            grouped_round_3[question["packetName"]].append(question)
        
        for packet_name in grouped_round_3:
            grouped_round_3[packet_name].sort(key=lambda x: x["stt"])

        for question in [question for question in question_list if question["round"] == 4]:
            grouped_round_4[question["difficulty"]].append(question)
        
        for packet_name in grouped_round_4:
            grouped_round_4[packet_name].sort(key=lambda x: x["stt"])

        round_1 = sorted([question for question in question_list if question["round"] == 1]  , key=lambda x: x["stt"]) #get question and sort by stt
        round_2 = sorted([question for question in question_list if question["round"] == 2]  , key=lambda x: x["stt"])
        round_3 = dict(grouped_round_3)
        round_4 = dict(grouped_round_4)
        turn = sorted([question for question in question_list if question["round"] == "turn"]  , key=lambda x: x["stt"])
        
        result = {
            "round_1": round_1,
            "round_2": round_2,
            "round_3": round_3,
            "round_4": round_4,
            "turn": turn
        }

        if "error" in tests:
            raise HTTPException(status_code=500, detail=tests["error"])
        if len(tests) == 0:
            raise HTTPException(status_code=404, detail="Test not found")
        return result
    
    
    def process_test_file(self, test_name: str, uid: str, file: UploadFile):
        existing_test = self.test_repository.get_test_by_test_name(test_name, uid)
        
        if existing_test:
            raise HTTPException(status_code=400, detail=f"Bộ đề với tên '{test_name}' đã tồn tại.")

        test_data = {
            "testId": test_id,
            "testName": test_name,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "owner": uid,
            "totalQuestions": 0,  
            "status": "active"
        }

        test_id = self.test_repository.create_test(test_data)

        self.test_repository.update_test(test_id, {"testId": test_id})

        process_excel_file(test_id,file,self.test_repository)
        

    def get_packet_name(self, test_data: dict) -> dict:
        try:
            packets = [item for item in test_data["round_3"]]
            return packets
        
        except:
            raise HTTPException(status_code=400, detail="Invalid round")

    def get_specific_question(
        self,
        test_data: dict,
        round: str,
        packet_name: Optional[str] = None,
        difficulty: Optional[str] = None,
        chunk: Optional[int] = None,
        question_number: Optional[str] = None,
        page: Optional[int] = 1,
        limit: Optional[int] = 1
    ) -> dict:

        try:
            question_index = int(question_number) - 1 if question_number is not None else None
            if question_index is not None and question_index < 0:
                raise ValueError("Question number must be positive")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question number")

        round_key = "turn" if round == "turn" else f"round_{round}"
        salt = "HTMNBK2025"
        logger.info(f"test_data {test_data}")
        if round_key not in test_data:
            raise HTTPException(status_code=400, detail="Invalid round")

        # Helper for pagination
        def paginate(data: list) -> list:
            start = (page - 1) * limit
            end = start + limit
            return data[start:end]

        if round in ["1", "2", "turn"]:
            questions = test_data[round_key]
            if question_index is not None:
                if 0 <= question_index < len(questions):
                    return questions[question_index]
                else:
                    raise HTTPException(status_code=404, detail="Question not found in this round")
            return paginate(questions)

        elif round == "3":
            if not packet_name:
                raise HTTPException(status_code=400, detail="packetName is required for round 3")
            if packet_name not in test_data["round_3"]:
                raise HTTPException(status_code=400, detail=f"Invalid packetName: {packet_name}")

            questions = []
            for q_obj in test_data["round_3"][packet_name]:
                questions.append(q_obj)

            if question_index is not None:
                if 0 <= question_index < len(questions):
                    return questions[question_index]
                else:
                    raise HTTPException(status_code=404, detail="Question not found in this packet")

            return paginate(questions)

        elif round == "4":
            if not difficulty:
                raise HTTPException(status_code=400, detail="difficulty is required for round 4")
            if difficulty not in ["Dễ", "Trung bình", "Khó"]:
                raise HTTPException(status_code=400, detail=f"Invalid difficulty: {difficulty}")
            logger.info(f"questions 3 :{test_data['round_4']}")

            # Get the actual questions list from the dictionary
            round_4_data = test_data["round_4"]
            if isinstance(round_4_data, dict):
                # If it's a dict, get the first value (the questions list)
                questions = list(round_4_data.values())[0]
            else:
                # If it's already a list
                questions = round_4_data

            logger.info(f"questions round 4 :{questions}")
            if question_index is not None:
                if 0 <= question_index < len(questions):
                    return questions[question_index]
                else:
                    raise HTTPException(status_code=404, detail="Question not found in this difficulty")

            return paginate(questions)

        else:
            raise HTTPException(status_code=400, detail="Invalid round")
        
    def get_question_without_answer(self,question, room_id):
        if isinstance(question, dict):
            current_correct_answer = question.get("answer")
            if current_correct_answer is not None:
                current_correct_answer = str(current_correct_answer).split("~/")

            self.realtime_question_repository.set_current_correct_answer(room_id, current_correct_answer)
            question_without_answer =  {key: value for key, value in question.items() if key != "answer"}


        elif isinstance(question, list):
            question_without_answer = [
                {key: value for key, value in q.items() if key != "answer"}
                for q in question if isinstance(q, dict)
            ]
        else:
            raise TypeError(f"Expected dict or list of dicts, but got {type(question)}")

        logger.info(f"question_without_answer {question_without_answer}")

        return question_without_answer
        
        
    def get_questions_by_round(self, test_data: dict, round: str, packet_name: Optional[str] = None, difficulty: Optional[str] = None) -> dict:

        round_key = f"round_{round}"
        if round_key not in test_data:
            raise HTTPException(status_code=400, detail="Invalid round")

        if round in ["1", "2"]:
            # Simple list lookup for round_1 and round_2
            # logger.info(f"questions index :{question_index}")
            questions = test_data[round_key]
            logger.info(f"questions :{test_data[round_key]}")
            try:
                return questions
            except:
                raise HTTPException(status_code=404, detail="Question not found in this round")
            
        
        elif round == "3":
            # Round 3 requires packetName
            if not packet_name:
                raise HTTPException(status_code=400, detail="packetName is required for round 3")
            logger.info(f"packet_name repr: {repr(packet_name)}")
            logger.info(f"questions index :{test_data['round_3']}")

            # if packet_name not in test_data["round_3"]:
            #     raise HTTPException(status_code=400, detail=f"Invalid packetName: {packet_name}")
            questions = test_data["round_3"][packet_name]
            try:
                return questions
            except:
                raise HTTPException(status_code=404, detail="Question not found in this round")
        
        elif round == "4":
            # Round 4 requires difficulty
            if not difficulty:
                raise HTTPException(status_code=400, detail="difficulty is required for round 4")
            if difficulty not in test_data["round_4"]:
                raise HTTPException(status_code=400, detail=f"Invalid difficulty: {difficulty}")
            
            questions = test_data["round_4"][difficulty]
            try:
                return questions
            except:
                raise HTTPException(status_code=404, detail="Question not found in this round")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid round")
        
    def update_question(self, question_id: str, updated_data: dict):
        try:
            self.question_repository.update_question(question_id, updated_data)            

        except Exception as e:
            logging.error(f"Unexpected error updating question {question_id}: {e}")
            return {"error": f"An unexpected error occurred: {e}"}

