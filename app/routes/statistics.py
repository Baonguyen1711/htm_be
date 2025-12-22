from fastapi import APIRouter
from starlette.requests import Request

from app.services.statistics_service import StatisticsService
import logging
import traceback
from ..helper.exception import handle_exceptions
from ..helper.host_only import host_only
from ..dependencies.router_dependencies import get_statistics_service
from ..models.statistics import Statistics, DetailStatistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

statistics_routers = APIRouter()

class StatisticsRouter:
    def __init__(self, statistics_service: StatisticsService = None):
        # FIXED: Accept actual service instance, not Depends() object
        self.statistics_service = statistics_service or get_statistics_service()
        self.router = APIRouter(prefix="/api/statistics")

        self.router.post("/add")(self.add_statistics)

        self.router.get("/test")(self.get_statistics_by_test_id)
        self.router.get("/")(self.get_statistics)

    @handle_exceptions
    def add_statistics(self, request: Request, test_id: str, data: DetailStatistics):
        user = request.state.user
        authenticated_uid = user["uid"]
        self.statistics_service.add_statistics(authenticated_uid, test_id, data)
        return {"message": f"Statistics added/updated for user_id: {authenticated_uid}"}
    
    @handle_exceptions
    def get_statistics(self, request: Request):
        user = request.state.user
        authenticated_uid = user["uid"]
        stats = self.statistics_service.get_all_statistics(authenticated_uid)
        return stats
    
    @handle_exceptions
    def get_statistics_by_test_id(self, request: Request, test_id: str):
        user = request.state.user
        authenticated_uid = user["uid"]
        stats = self.statistics_service.get_statistics(authenticated_uid, test_id)
        return stats

    

       


