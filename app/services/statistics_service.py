import logging
from fastapi import HTTPException, status, Depends
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from app.dependencies.service_dependencies import get_statistics_repository
from app.repositories.firestore.statistics_repository import StatisticsRepository
from app.models.statistics import DetailStatistics

class StatisticsService:
    def __init__(self, statistics_repository: StatisticsRepository = Depends(get_statistics_repository)):
        self.statistics_repository = statistics_repository

    def add_statistics(self, user_id: str, test_id: str, data: DetailStatistics):
        try:
            self.statistics_repository.add_statistics(user_id, test_id, data )
            logger.info(f"Statistics added/updated for user_id: {user_id}")
        except Exception as e:
            logger.error(f"Error adding/updating statistics for user_id {user_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add/update statistics")

    def get_statistics(self, user_id: str, test_id: str):
        try:
            stats = self.statistics_repository.get_statistics(user_id, test_id)
            logger.info(f"Statistics retrieved for user_id: {user_id} with test id {test_id}")
            return stats
        except Exception as e:
            logger.error(f"Error retrieving statistics for user_id {user_id} with test id {test_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve statistics")

    def get_all_statistics(self, user_id: str):
        try:
            stats = self.statistics_repository.get_statistics_by_user(user_id)
            logger.info(f"Statistics retrieved for user_id: {user_id}")
            return stats
        except Exception as e:
            logger.error(f"Error retrieving statistics for user_id {user_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve statistics")