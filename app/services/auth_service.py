from fastapi import HTTPException
from firebase_admin import auth
import jwt
import time
import os

def verify_token(token: str):
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        return decoded_token  # Return the decoded token, which includes the user's uid and email.
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    


def create_room_token(room_id: str, role: str, user_id: str = None):
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    payload = {
        "roomId": room_id,
        "role": role,
        "userId": user_id or "anon_" + str(int(time.time() * 1000)),
        "exp": time.time() + 30*60  
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token