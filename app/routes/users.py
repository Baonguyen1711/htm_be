from fastapi import APIRouter, HTTPException
from app.models import User
from app.services.firestore_service import add_user_to_firestore, get_user_from_firestore
from app.services.realtime_service import send_realtime_notification
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
users_router = APIRouter()

# API: Tạo người dùng
@users_router.post("/users/")
def create_user(user: User):
    add_user_to_firestore(user.id, user.dict())
    send_realtime_notification({"message": f"User {user.name} has been created"})
    return {"message": "User created successfully", "user": user.dict()}

# API: Lấy thông tin người dùng
@users_router.get("/users/{user_id}")
def read_user(user_id: str):
    user = get_user_from_firestore(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
