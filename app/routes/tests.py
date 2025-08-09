from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from fastapi import FastAPI, UploadFile
from starlette.requests import Request

from ..models.questions import UpdateQuestionBody, Answer, Grid, PlacementArray
from ..models.scores import Score, ScoreRule
from fastapi.encoders import jsonable_encoder
import logging
import traceback
from app.stores.player_store import get_player_info
from app.services.firestore_service import upload_test_to_firestore, get_test_by_name, get_test_name_by_user_id, update_question, upload_single_question_to_firestore
from ..services.test_service import TestService
from ..helper.exception import handle_exceptions
from ..helper.host_only import host_only
# FIXED: Move import outside of class to fix circular import
from ..dependencies.router_dependencies import get_test_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestRouter:

    def __init__(self, test_service: TestService = None):
        # FIXED: Accept actual service instance, not Depends() object
        self.test_service = test_service or get_test_service()
        self.router = APIRouter(prefix="/api/test")

        #GET
        self.router.get("/user")(self.get_test_name_by_user_id)

        #POST
        self.router.post("/upload")(self.process_file)

        #DELETE
        self.router.put("/question/update")(self.update_question_document)
        
        self.router.get("/")(self.get_test)


    @handle_exceptions
    @host_only
    def update_question_document(self, request: Request, question_id: str, body: UpdateQuestionBody):
        logger.info("Updating question")
        updated_data = jsonable_encoder(body)
        result = self.test_service.update_question(question_id, updated_data)
       
        return result
                

    @handle_exceptions
    @host_only
    def get_test_name_by_user_id(self, request: Request):
        user = request.state.user
        authenticated_uid = user["uid"]

        test_list = self.test_service.get_test_name_by_user_id(authenticated_uid)
        
        return test_list


    @handle_exceptions
    @host_only
    def get_test(self, test_name: str, request: Request):
        user = request.state.user
        authenticated_uid = user["uid"]

        test_list = self.test_service.get_test_for_each_round(authenticated_uid, test_name)
        return test_list

    @handle_exceptions
    @host_only
    async def process_file(self, test_name: str, request: Request, file: UploadFile = File(...)):

        logger.info(f"Received upload request - test_name: {test_name}")
        logger.info(f"File info: filename={file.filename}, content_type={file.content_type}, size={file.size if hasattr(file, 'size') else 'unknown'}")

        user = request.state.user
        authenticated_uid = user["uid"]

        logger.info(f"authenticated_uid: {authenticated_uid}")
        logger.info(f"Processing file: {file.filename} for test: {test_name}")

        result = await self.test_service.process_test_file(test_name, authenticated_uid, file)

        logger.info(f"File processing completed successfully for test: {test_name}")
        logger.info(f"Service result: {result}")

        response_data = {
            "message": f"Test '{test_name}' uploaded successfully",
            "test_name": test_name,
            "filename": file.filename,
            "result": result
        }

        logger.info(f"Returning response: {response_data}")
        return response_data



    # @handle_exceptions
    # async def add_new_question_to_test(question: UpdateQuestionRequest):
    #     try:

    #         await upload_single_question_to_firestore(question)
            
    #     except HTTPException as http_exc:
    #         raise http_exc  # Re-raise HTTPException to let FastAPI set the status code
    #     except Exception as e:
    #         logger.error(f"Error processing Excel file: {str(e)}")
    #         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
