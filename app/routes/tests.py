from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi import FastAPI, Depends, UploadFile
from starlette.requests import Request
from firebase_admin import auth
from ..database import db
from ..services.auth_service import verify_token
from google.cloud import firestore
from collections import defaultdict
from ..models.questions import UpdateQuestionRequest, Answer
from fastapi.encoders import jsonable_encoder
import shutil
from openpyxl import load_workbook
from io import BytesIO
from typing import Optional
import logging
import traceback
from app.services.firestore_service import upload_test_to_firestore, get_test_by_name, get_test_name_by_user_id, update_question
from ..services.test_service import process_test_data, get_specific_question
from ..services.realtime_service import send_question_to_player, send_answer_to_player, start_time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

test_routers = APIRouter()

@test_routers.put("/api/test/update/{question_id}")
def update_question_document(question_id, request: UpdateQuestionRequest):
    update_data = jsonable_encoder(request)
    logger.info(f"updated_data {update_data}")
    if not request:
        raise HTTPException(status_code=400, detail="No fields provided to update.")
    result = update_question(question_id, update_data)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@test_routers.get("/api/test/user")
def read_test_by_user_id(request: Request):
    user = request.state.user
    authenticated_uid = user["uid"]
    logger.info(f"authenticated_uid: {authenticated_uid}")

    # if user_id != authenticated_uid:
    #     raise HTTPException(status_code=403, detail="Unauthorized access to this user's tests")
    
    test_list = get_test_name_by_user_id(authenticated_uid)
    if "error" in test_list:
        raise HTTPException(status_code=500, detail=test_list["error"])
    if len(test_list) == 0:
        raise HTTPException(status_code=404, detail="no test found")
    return test_list


@test_routers.get("/api/test/question")
def get_question_one_by_one(test_name:str, question_number: str,round: str, room_id: str,request: Request, packet_name: Optional[str] = None, difficulty: Optional[str] = None):
    try:
        user = request.state.user
        authenticated_uid = user["uid"]
        result = process_test_data(authenticated_uid, test_name)

        try:
            logger.info("Attempting to create reference to Firebase")
            question = get_specific_question(result,question_number,round,packet_name, difficulty)
            logger.info("get question correctly")
            

            # Tiếp tục logic của bạn
        
        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  # Ném lại lỗi để xử lý ở tầng trên nếu cần

        try:
            logger.info("Attempting to create reference to Firebase")
            question_without_answer = {key: value for key , value in question.items() if key!="answer"}
            logger.info(f"question_with_answer {question_without_answer}")
            

            # Tiếp tục logic của bạn
        
        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  # Ném lại lỗi để xử lý ở tầng trên nếu cần


        try:
            logger.info("Attempting to create reference to Firebase")
            send_question_to_player(question_without_answer,room_id)
            logger.info("send successfully")
            

            # Tiếp tục logic của bạn
        
        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  # Ném lại lỗi để xử lý ở tầng trên nếu cần
        
        
    except HTTPException as http_exc:
        raise http_exc  # Re-raise HTTPException to let FastAPI set the status code
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    return question

@test_routers.post("/api/test/answer")
def get_question_one_by_one(room_id: str,answer:Answer, request: Request):
    try:
        user = request.state.user
        authenticated_uid = user["uid"]
        if not authenticated_uid:
            logger.info(f"abc")
            raise HTTPException(status_code=401, detail="Unauthorized: User ID not found")
        

        try:
            logger.info("Attempting to send answer to player")
            send_answer_to_player(answer.answer,room_id)
            logger.info("send answer correctly")

        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  
    except HTTPException as http_exc:
        raise http_exc  # Re-raise HTTPException to let FastAPI set the status code
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
@test_routers.post("/api/test/time")
def get_question_one_by_one(room_id: str,request: Request):
    try:
        user = request.state.user
        authenticated_uid = user["uid"]
        if not authenticated_uid:
            logger.info(f"abc")
            raise HTTPException(status_code=401, detail="Unauthorized: User ID not found")
        
        try:
            logger.info("Attempting to start time")
            start_time(room_id)
            logger.info("time started")

        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  
    except HTTPException as http_exc:
        raise http_exc  # Re-raise HTTPException to let FastAPI set the status code
    except Exception as e:

        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

        

@test_routers.get("/api/test/{test_name}")
def read_test(test_name: str, request: Request):
    user = request.state.user
    authenticated_uid = user["uid"]
    test = get_test_by_name(authenticated_uid, test_name)[0]["questions"]
    logger.info(f"test: {test}")
    grouped_round_3 = defaultdict(list)
    for question in [question for question in test if question["round"] == 3]:
        grouped_round_3[question["packetName"]].append(question)
    
    for packet_name in grouped_round_3:
        grouped_round_3[packet_name].sort(key=lambda x: x["stt"])

    grouped_round_4 = defaultdict(list)
    for question in [question for question in test if question["round"] == 4]:
        grouped_round_4[question["difficulty"]].append(question)
    
    for packet_name in grouped_round_4:
        grouped_round_4[packet_name].sort(key=lambda x: x["stt"])

    round_1 = sorted([question for question in test if question["round"] == 1]  , key=lambda x: x["stt"]) #get question and sort by stt
    round_2 = sorted([question for question in test if question["round"] == 2]  , key=lambda x: x["stt"])
    round_3 = dict(grouped_round_3)
    round_4 = dict(grouped_round_4)
    
    result = {
        "round_1": round_1,
        "round_2": round_2,
        "round_3": round_3,
        "round_4": round_4
    }

    if "error" in test:
        raise HTTPException(status_code=500, detail=test["error"])
    if len(test) == 0:
        raise HTTPException(status_code=404, detail="Test not found")
    return result


@test_routers.post("/api/test/upload")
async def process_file(test_name: str , request: Request, file: UploadFile = File(...)):
    try:
        # Kiểm tra xem test_name đã tồn tại chưa
        user = request.state.user
        authenticated_uid = user["uid"]
        print(f"user: {user}")
        logger.info(f"authenticated_uid: {authenticated_uid}")
        existing_test = db.collection("tests").where("testName", "==", test_name).limit(1).get()
        if existing_test:
            raise HTTPException(status_code=400, detail=f"Bộ đề với tên '{test_name}' đã tồn tại.")

        # Tạo một document trong "tests" cho toàn bộ file upload
        test_ref = db.collection("tests").document()  
        test_id = test_ref.id
        test_data = {
            "testId": test_id,
            "testName": test_name,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "owner": authenticated_uid,
            "totalQuestions": 0,  
            "status": "active"
        }
        test_ref.set(test_data)
        # Đọc nội dung file vào bộ nhớ
        contents = await file.read()

        # Tải file Excel từ nội dung trong bộ nhớ
        workbook = load_workbook(BytesIO(contents))


        # Kết quả tổng hợp từ tất cả các sheet
        result = {
            "filename": file.filename,
            "sheets": {}
        }

        # Duyệt qua từng sheet trong workbook
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            logger.info(f"sheet: {sheet}")
            data = []

            # Đọc từng dòng trong sheet
            for row in sheet.iter_rows(values_only=True):
                data.append(row)

            # Xử lý dữ liệu theo tên sheet bằng match-case
            match sheet_name.lower():  # Chuyển thành chữ thường để tránh lỗi
                case "round1":
                    # Xử lý cho Round 1 (ví dụ: chỉ có question và answer)
                    processed_data = [
                        {
                            "stt": int(row[0]) if row[0] else None,  # Cột STT
                            "question": row[1],                      # Cột Question
                            "answer": row[2], 
                            "type": row[3],                          # Cột Answer
                            "imgUrl": row[4]                         # Cột ImgUrl
                        }
                        for row in data[1:]  # Bỏ header
                        if row[1] and row[2]  # Kiểm tra question và answer không null
                    ]

                    logger.info(f"processed_data: {processed_data}")
                    result["sheets"]["round1"] = {
                        "sheet_name": sheet_name,
                        "content": processed_data,
                        "round": 1
                    }

                    print(processed_data)

                    # Gọi hàm upload ngay sau khi xử lý dữ liệu
                    if processed_data:  # Chỉ upload nếu có dữ liệu
                        upload_result = upload_test_to_firestore(
                            rounds=1, 
                            questions=processed_data,  # Dữ liệu câu hỏi đã xử lý
                            test_id=test_id
                        )
                        result["sheets"]["round1"]["upload_result"] = upload_result
                    else:
                        result["sheets"]["round1"]["upload_result"] = {
                            "message": "Không có dữ liệu hợp lệ để upload cho sheet round1."
                        }

                case "round2":

                    # Xử lý cho Round 2 (ví dụ: thêm images)
                    processed_data = [
                        {
                            "stt": int(row[0]) if row[0] else None,  # Cột STT,
                            "question": row[1],                      # Cột Question
                            "answer": row[2], 
                        }
                        for row in data[1:] if row[1] and row[2] #check null
                    ]

                    logger.info(f"processed_data: {processed_data}")
                    result["sheets"]["round2"] = {
                        "sheet_name": sheet_name,
                        "content": processed_data,
                        "round": 2
                    }

                    if processed_data:  # Chỉ upload nếu có dữ liệu
                        upload_result = upload_test_to_firestore(
                            rounds=2, 
                            questions=processed_data,  # Dữ liệu câu hỏi đã xử lý
                            test_id=test_id
                        )
                        result["sheets"]["round2"]["upload_result"] = upload_result
                    else:
                        result["sheets"]["round2"]["upload_result"] = {
                            "message": "Không có dữ liệu hợp lệ để upload cho sheet round2."
                        }

                case "round3":
                    # Xử lý cho Round 1 (ví dụ: chỉ có question và answer)
                    packet_name = ""
                    # Xử lý dữ liệu từ sheet
                    processed_data = []
                    for row in data[1:]:  # Bỏ header
                        if row[0] == "Tên gói":  
                            packet_name = row[1]  
                            continue  
                        
                        if row[1] and row[2]:
                            processed_data.append({
                                "stt": int(row[0]) if row[0] else None,  # Cột STT
                                "question": row[1],                      # Cột Question
                                "answer": row[2],                        # Cột Answer
                                "packetName": packet_name               # Thêm packet_name vào object
                            })

                    logger.info(f"processed_data: {processed_data}")
                    result["sheets"]["round3"] = {
                        "sheet_name": sheet_name,
                        "content": processed_data,
                        "round": 3
                    }

                    print(processed_data)

                    # Gọi hàm upload ngay sau khi xử lý dữ liệu
                    if processed_data:  # Chỉ upload nếu có dữ liệu
                        upload_result = upload_test_to_firestore(
                            rounds=3, 
                            questions=processed_data,  # Dữ liệu câu hỏi đã xử lý
                            test_id=test_id
                        )
                        result["sheets"]["round3"]["upload_result"] = upload_result
                    else:
                        result["sheets"]["round3"]["upload_result"] = {
                            "message": "Không có dữ liệu hợp lệ để upload cho sheet round3."
                        }

                case "round4":
                    difficulty = ""
                    # Xử lý dữ liệu từ sheet
                    processed_data = []
                    for row in data[1:]:  # Bỏ header
                        logger.info(f"row: {row}")
                        if row[0] == "Mức độ":  
                            difficulty = row[1] 
                            continue  
                        
                        if row[1] and row[2]:
                            processed_data.append({
                                "stt": int(row[0]) if row[0] else None,  # Cột STT
                                "question": row[1],                      # Cột Question
                                "answer": row[2], 
                                "url": row[3],                       # Cột Answer
                                "difficulty": difficulty               
                            })

                    logger.info(f"processed_data: {processed_data}")
                    result["sheets"]["round4"] = {
                        "sheet_name": sheet_name,
                        "content": processed_data,
                        "round": 4
                    }

                    print(processed_data)

                    # Gọi hàm upload ngay sau khi xử lý dữ liệu
                    
                    if processed_data:  # Chỉ upload nếu có dữ liệu
                        upload_result = upload_test_to_firestore(
                            rounds=4, 
                            questions=processed_data,  # Dữ liệu câu hỏi đã xử lý
                            test_id=test_id
                        )
                        result["sheets"]["round4"]["upload_result"] = upload_result
                    else:
                        result["sheets"]["round4"]["upload_result"] = {
                            "message": "Không có dữ liệu hợp lệ để upload cho sheet round4."
                        }


                case _:
                    # Xử lý mặc định nếu sheet không khớp
                    logger.warning(f"Sheet không xác định: {sheet_name}")
                    result["sheets"][sheet_name] = {
                        "sheet_name": sheet_name,
                        "content": data,
                        "round": None
                    }

            logger.info(f"Đã xử lý sheet: {sheet_name} với {len(data)} dòng")

        return result

    except HTTPException as http_exc:
        raise http_exc  # Re-raise HTTPException to let FastAPI set the status code
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    finally:
        await file.close()


