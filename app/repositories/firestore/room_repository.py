from .base import BaseRepository

class RoomRepository(BaseRepository):
    def __init__(self):
        super().__init__("rooms")
    
    def get_room_by_id(self, room_id):
        return self.get_document(room_id)
    
    def get_rooms_by_user_id(self, user_id):
        filters = [("ownerId", "==", user_id)]
        return self.get_documents_by_filter(filters)
    
    def create_room(self, data, room_id):
        room = {
            **data,
            "roomId": room_id
        }
        return self.create_new_document(room, room_id)
    
    def update_room(self, room_id, data):
        self.update_document(room_id, data)

    
            

    
