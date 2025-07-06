# Process and cache test data

from collections import defaultdict
import logging

from app.services.firestore_service import upload_test_to_firestore, get_test_by_name, get_test_name_by_user_id, update_question, get_test_by_test_id
from .cache_service import get_cached_test, set_cached_test, clear_cached_test
from typing import Optional
from fastapi import HTTPException, status, Depends
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_test_data(uid: str, test_name: str):

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

    set_cached_test(uid, test_name, result)
    return result

def get_packet_name(test_data: dict) -> dict:
    try:
        packets = [item for item in test_data["round_3"]]
        return packets
    
    except:
        raise HTTPException(status_code=400, detail="Invalid round")

def get_specific_question(
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
            # original_question = q_obj.get("question")
            # if not original_question:
            #     raise HTTPException(status_code=500, detail="Missing question field in packet")

            # salted = salt + original_question
            # encoded_question = base64.b64encode(salted.encode()).decode()

            # obfuscated_obj = dict(q_obj)
            # obfuscated_obj["question"] = encoded_question
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

        # stt = question_index
        # if difficulty == "Dễ":
        #     stt = stt
        # elif difficulty == "Trung bình":
        #     stt = stt + 20
        # else:
        #     stt = stt + 40
        if question_index is not None:
            if 0 <= question_index < len(questions):
                return questions[question_index]
            else:
                raise HTTPException(status_code=404, detail="Question not found in this difficulty")

        return paginate(questions)

    else:
        raise HTTPException(status_code=400, detail="Invalid round")
    try:
        if question_number is not None:
            question_index = int(question_number) - 1 
            if question_index < 0:
                raise ValueError("Question number must be positive")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question number")

    round_key = f"round_{round}"
    salt = "HTMNBK2025"
    if round_key not in test_data:
        raise HTTPException(status_code=400, detail="Invalid round")

    if round in ["1", "2"]:
        # Simple list lookup for round_1 and round_2
        logger.info(f"questions index :{question_index}")
        questions = test_data[round_key]
        logger.info(f"questions :{test_data[round_key]}")
        if 0 <= question_index < len(questions):
            logger.info(f"questions[question_index] :{questions[question_index]}")
            return questions[question_index]
        else:
            raise HTTPException(status_code=404, detail="Question not found in this round")
        
    
    elif round == "3":
        # Round 3 requires packetName
        if not packet_name:
            raise HTTPException(status_code=400, detail="packetName is required for round 3")
        if packet_name not in test_data["round_3"]:
            raise HTTPException(status_code=400, detail=f"Invalid packetName: {packet_name}")
        
        questions = []
        for q_obj in test_data["round_3"][packet_name]:
        # Encode only the question field
            original_question = q_obj.get("question")
            if not original_question:
                raise HTTPException(status_code=500, detail="Missing question field in packet")

            salted = salt + original_question
            encoded_question = base64.b64encode(salted.encode()).decode()

            # Copy the rest of the object and replace question
            obfuscated_obj = dict(q_obj)  # shallow copy
            obfuscated_obj["question"] = encoded_question
            questions.append(obfuscated_obj)
    
        return questions

        # if 0 <= question_index < len(questions):
        #     return questions[question_index]
        # else:
        #     raise HTTPException(status_code=404, detail="Question not found in this packet")
    
    elif round == "4":
        # Round 4 requires difficulty
        logger.info(f"questions :{test_data['round_4']}")
        if not difficulty:
            raise HTTPException(status_code=400, detail="difficulty is required for round 4")
        if difficulty not in test_data["round_4"]:
            raise HTTPException(status_code=400, detail=f"Invalid difficulty: {difficulty}")
        

        questions = test_data["round_4"][difficulty]
        if 0 <= question_index < len(questions):
            return questions[question_index]
        else:
            raise HTTPException(status_code=404, detail="Question not found in this difficulty")
    
    else:
        raise HTTPException(status_code=400, detail="Invalid round")
    
def get_questions_by_round(test_data: dict, round: str, packet_name: Optional[str] = None, difficulty: Optional[str] = None) -> dict:

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

