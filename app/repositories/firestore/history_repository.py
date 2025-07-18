from ...models.history import History
from .base import BaseRepository

class HistoryRepository(BaseRepository):
    def __init__(self):
        super().__init__("histories")
    
    def update_history(self, user_id: str, data: History):
        self.update_document(user_id, data)

    def get_history_by_user_id(self, user_id: str):
        return self.get_document(user_id)