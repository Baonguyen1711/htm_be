from firebase_admin import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeBaseRepository:
    def __init__(self):
        self.database = db
        self.base_path = "rooms"

    def set_to_path(self, path, data):
        logger.info(f"Setting data to path {self.base_path}/{path}: {data}")
        ref = self.database.reference(f"{self.base_path}/{path}")
        ref.set(data)

    def set_to_path_with_child_node(self, path, data):
        logger.info(f"Setting data to path {self.base_path}/{path}: {data}")
        ref = self.database.reference(f"{self.base_path}/{path}").push()
        ref.set(data)
        return ref.path

    def read_from_path(self, path):
        logger.info(f"Reading data from path {self.base_path}/{path}")
        ref = self.database.reference(f"{self.base_path}/{path}")
        return ref.get()
    
    def delete_path(self, path):
        logger.info(f"Reading data from path {self.base_path}/{path}")
        ref = self.database.reference(f"{self.base_path}/{path}")
        ref.delete()
    
    def do_transaction(self, path, function):
        ref = self.database.reference(f"{self.base_path}/{path}")
        
        result = ref.transaction(function)

        return result