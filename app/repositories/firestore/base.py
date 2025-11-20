import bcrypt
from ...database import db
from typing import Optional

class BaseRepository:
    def __init__(self, collection_name: str, database):
        self.database = database
        self.collection = self.database.collection(collection_name)

    #create a new document with optional document_id
    def create_new_document(self, data, document_id=None):        
        if document_id:
            doc_ref = self.collection.document(document_id)
        else:
            doc_ref = self.collection.document()

        #set the data to the document
        doc_ref.set(data)

        return doc_ref.id
    
    # get a document with document_id
    def get_document(self, document_id):
        doc_ref = self.collection.document(document_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    
    def get_all_documents(self):
        docs = self.collection.stream()
        return [doc.to_dict() for doc in docs]

    def get_documents_by_filter(self, filters: list[tuple[str, str, any]], limit : Optional[int] = None):
        query = self.collection
        for filter_field, operator, filter_value in filters:
            query = query.where(field_path=filter_field, op_string=operator, value=filter_value)

        if limit is not None:
            query = query.limit(limit)
            
        docs = query.stream()
        return [doc.to_dict() for doc in docs]

    def update_document(self, document_id, data):
        doc_ref = self.collection.document(document_id)
        doc_ref.update(data)

    def delete_document(self, document_id):
        doc_ref = self.collection.document(document_id)
        doc_ref.delete()

    