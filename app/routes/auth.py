from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import Response
import logging
from ..services.auth_service import AuthService
from ..helper.exception import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
auth_routers = APIRouter()

ACCESS_TOKEN_EXPIRE_SECONDS = 30 * 60  # 30 minutes 
REFRESH_TOKEN_EXPIRE_SECONDS = 4* 60 * 60  # 7 days

class AuthRouter:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

        self.router = APIRouter(prefix="/api/auth")

        self.router.post("/access_token")(self.generate_tokens)
        self.router.post("/verify")(self.verify_room_token)
        self.router.post("/refresh")(self.refresh_access_token)
        self.router.post("/isHost")(self.verify_is_host)
        self.router.post("/token")(self.authenticate)
        self.router.post("/logout")(self.logout)

    @handle_exceptions
    async def generate_tokens(self, request: Request):
        access_token, refresh_token = await self.auth_service.generate_tokens(request)
        response = JSONResponse({
            "accessToken": access_token,
        })

        response.set_cookie(
            key="refreshToken",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=REFRESH_TOKEN_EXPIRE_SECONDS
        )

        return response

    @handle_exceptions
    async def verify_room_token(self, request: Request):
        payload = await self.auth_service.verify_room_token(request)
        return payload
        
    @handle_exceptions
    async def refresh_access_token(self, request: Request):
        access_token = await self.auth_service.refresh_access_token(request)
        return JSONResponse({
            "accessToken": access_token
        })
        
    @handle_exceptions
    async def verify_is_host(self, request: Request):
        user = request.state.user
        authenticated_uid = user["uid"]
        is_host_user = await self.auth_service.verify_is_host(authenticated_uid)

        return is_host_user

    @handle_exceptions
    async def authenticate(self, request: Request, response: Response):
        api_token, decoded_token = await self.auth_service.authenticate(request)

        response.set_cookie(
            key="authToken",
            value=api_token,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=60*60*6  # 7 days 
        )

        return {"message": "Authenticated", "user": decoded_token}
       

    @handle_exceptions
    async def logout(response: Response):
        try:
            # Clear the httpOnly cookies by setting them to expire immediately
            response.set_cookie(
                key="refreshToken",
                value="",
                httponly=True,
                secure=True,
                samesite="None",
                max_age=0  # Expire immediately
            )

            response.set_cookie(
                key="authToken",
                value="",
                httponly=True,
                secure=True,
                samesite="None",
                max_age=0  # Expire immediately
            )

            return {"message": "Logged out successfully"}
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {"error": "Logout failed"}
