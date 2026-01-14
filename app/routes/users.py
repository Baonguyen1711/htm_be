from fastapi import APIRouter, HTTPException, Request
from app.helper.exception import handle_exceptions
from app.models import User
from app.services.auth_service import AuthService
from ..dependencies.router_dependencies import get_auth_service
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
users_router = APIRouter()

class AuthRouter:
    def __init__(self, auth_service: AuthService = None):
        # FIXED: Accept actual service instance, not Depends() object
        self.auth_service = auth_service or get_auth_service()

        self.router = APIRouter(prefix="/api/users")

        self.router.post("/create/host")(self.create_new_host_user)
        self.router.post("/create")(self.create_new_normal_user)

    