from ...models.history import History
from .base import BaseRepository
from datetime import datetime, timezone

class HistoryRepository(BaseRepository):
    def __init__(self, database):
        super().__init__("histories", database)
    
    def create_history(self, user_id: str, data: dict):
        """Create a new history entry with random document ID and include uid field"""
        # Add uid and timestamp to the data
        data_with_metadata = {
            **data,
            "uid": user_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        # Create document with random ID (no document_id parameter)
        return self.create_new_document(data_with_metadata)

    def get_history_by_user_id(self, user_id: str):
        """Get all history entries for a specific user"""
        filters = [("uid", "==", user_id)]
        return self.get_documents_by_filter(filters)