from fastapi import logger
from .base import BaseRepository
import logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from app.models.statistics import DetailStatistics, Statistics, UserStatistics

class StatisticsRepository(BaseRepository):
    def __init__(self, database):
        super().__init__("statistics", database)

    def add_statistics(
        self,
        user_id: str,
        test_name: str,
        data: DetailStatistics
    ):
        logger.info(f"user_id {user_id}")

        test_ref = (
            self.database
            .collection("statistics")
            .document(user_id)
            .collection("tests")
            .document(test_name)
        )

        # 🔴 BẮT BUỘC tạo document test
        test_ref.set({
            "test_name": test_name,
        }, merge=True)

        payload = (
            data.model_dump()
            if hasattr(data, "model_dump")
            else data
        )

        # Sau đó mới add records
        test_ref.collection("records").add(payload)

    def get_statistics_by_user(self, user_id: str):
        logger.info(f"uid for statistic {user_id}")
        tests_ref = (
            self.database
            .collection("statistics")
            .document(user_id)
            .collection("tests")
        )

        result = []

        logger.info(f"tests_ref {tests_ref}")
        logger.info(f"tests_ref.stream() {tests_ref.stream()}")

        for test_doc in tests_ref.stream():
            records_ref = test_doc.reference.collection("records")
            records = [doc.to_dict() for doc in records_ref.stream()]

            correct = sum(1 for r in records if r.get("is_correct"))
            total = len(records)

            test_data = test_doc.to_dict() or {}

            result.append({
                "test_id": test_doc.id,
                "test_name": test_data.get("test_name", f"Test {test_doc.id[:6]}"),
                "total_questions": total,
                "correct": correct,
                "wrong": total - correct,
                "accuracy": round((correct / total) * 100) if total else 0,
                "records": records
            })


        return result
    
    def get_statistics(self, user_id: str, test_id: str):
        records_ref = (
            self.database
            .collection("statistics")
            .document(user_id)
            .collection("tests")
            .document(test_id)
            .collection("records")
        )

        return [doc.to_dict() for doc in records_ref.stream()]



