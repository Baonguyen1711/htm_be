from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict
from app.services.s3_service import S3Service
from app.services.firestore_service import save_file_key_for_user
from starlette.requests import Request

class S3Router:
    def __init__(self, s3_service: S3Service):
        self.s3_service = s3_service
        self.router = APIRouter()

        self.router.get("/api/s3/presigned-url")(self.generate_presigned_url)
        self.router.delete("/api/s3/files/{key}")(self.delete_file)
        self.router.get("/api/s3/files/{key}")(self.download_file)
        self.router.post("/api/s3/save-file-key")(self.save_file_key) 

    def generate_presigned_url(self, extension: str = Query(...), content_type: str = Query(...)) -> Dict[str, str]:
        try:
            result = self.s3_service.presigned_url(extension, content_type)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def delete_file(self, key: str):
        try:
            self.s3_service.delete_file(key)
            return {"message": f"File {key} deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def download_file(self, key: str):
        try:
            result = self.s3_service.download_file(key)
            return {
                "contentType": result["contentType"],
                "key": result["key"],
                "data": result["buffer"].decode("utf-8", errors="ignore")  # careful with binary data!
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    def save_file_key(self, request: Request, data: Dict = Body(...)):
        """
        Example request body:
        {
            "userId": "abc123",
            "fileKey": "uuid-filename.jpg"
            "description": "avatar"
        }
        """
        try:
            user = request.state.user  
            authenticated_uid = user.get("uid")
            description = data.get("description")
            file_key = data.get("fileKey")

            if not authenticated_uid or not file_key:
                raise HTTPException(status_code=400, detail="Missing userId or fileKey")

            # Save file key to Firestore/DB/etc.
            save_file_key_for_user(authenticated_uid, file_key, description)

            return {"message": "File key saved successfully", "userId": authenticated_uid, "fileKey": file_key}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
