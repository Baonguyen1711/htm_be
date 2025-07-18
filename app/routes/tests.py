from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi import FastAPI, Depends, UploadFile
from starlette.requests import Request

from ..models.questions import UpdateQuestionRequest, Answer, Grid, PlacementArray
from ..models.scores import Score, ScoreRule
from fastapi.encoders import jsonable_encoder
import logging
import traceback
from app.stores.player_store import get_player_info
from app.services.firestore_service import upload_test_to_firestore, get_test_by_name, get_test_name_by_user_id, update_question, upload_single_question_to_firestore
from ..services.test_service import TestService
from ..helper.exception import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestRouter:
    def __init__(self, test_service: TestService):
        self.test_service = test_service
        self.router = APIRouter(prefix="/api/test")

        #GET
        self.router.get("/user")(self.get_test_name_by_user_id)
        self.router.get("/{test_name}")(self.get_test)

        #POST
        self.router.post("/upload")(self.process_file)

        #DELETE
        self.router.put("/update/{question_id}")(self.update_question_document)
        


    @handle_exceptions
    def update_question_document(self, question_id, request: UpdateQuestionRequest):
        logger.info("Updating question")
        updated_data = jsonable_encoder(request)
        result = self.test_service.update_question(question_id, updated_data)
       
        return result
                

    @handle_exceptions
    def get_test_name_by_user_id(self, request: Request):
        user = request.state.user
        authenticated_uid = user["uid"]

        test_list = self.test_service.get_test_name_by_user_id(authenticated_uid)
        
        return test_list


    @handle_exceptions
    def get_test(self, test_name: str, request: Request):
        user = request.state.user
        authenticated_uid = user["uid"]

        test_list = self.test_service.get_test_for_each_round(authenticated_uid, test_name)
        return test_list

    @handle_exceptions
    async def process_file(self, test_name: str , request: Request, file: UploadFile = File(...)):

        user = request.state.user
        authenticated_uid = user["uid"]

        logger.info(f"authenticated_uid: {authenticated_uid}")

        self.test_service.process_test_file(test_name, authenticated_uid, file)



    # @handle_exceptions
    # async def add_new_question_to_test(question: UpdateQuestionRequest):
    #     try:

    #         await upload_single_question_to_firestore(question)
            
    #     except HTTPException as http_exc:
    #         raise http_exc  # Re-raise HTTPException to let FastAPI set the status code
    #     except Exception as e:
    #         logger.error(f"Error processing Excel file: {str(e)}")
    #         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
