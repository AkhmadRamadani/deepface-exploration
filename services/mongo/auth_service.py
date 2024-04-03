from pymongo import MongoClient
from bson.objectid import ObjectId


class AuthService:
    def __init__(self, mongo_client):
        self.client = mongo_client
        self.db = self.client["face_recognition"]
        self.collection = self.db["users"]

    def get_user(self, user_id):
        user = self.collection.find_one({"_id": user_id})
        return user
    
