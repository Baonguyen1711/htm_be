# middleware/auth.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import HTTPException, status, Depends
from firebase_admin import auth
from ..database import db

import logging

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip middleware for preflight OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)
        # Skip middleware for public routes
        # if request.url.path in ["/public-route", "/health-check"]:
        #     return await call_next(request)
        logger.info(f"request: {request.headers.get('authorization')}")
        # Extract the Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer"):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header.split(" ")[1]

        try:
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(token)
            
            email = decoded_token.get("email")
            logger.info(f"email: {email}")
            # Check Firestore for the whitelisted email
            doc_ref = db.collection("allowed_emails").document(email)
            doc = doc_ref.get()
            logger.info(f"doc: {doc}")
            if not doc.exists:
                raise HTTPException(status_code=403, detail="Email not authorized")
            
            # Proceed to the next middleware/endpoint
            request.state.user = decoded_token  # You can store user info in the request state
            return await call_next(request)

        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    