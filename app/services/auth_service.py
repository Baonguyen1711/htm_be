from fastapi import HTTPException
from firebase_admin import auth


def verify_token(token: str):
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        return decoded_token  # Return the decoded token, which includes the user's uid and email.
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")