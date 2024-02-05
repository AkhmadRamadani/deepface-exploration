from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import dumps
from flask import jsonify
import json

class MongoService:
    uri = "mongodb://venturo:Bismillah2023*@103.125.36.80:14045/"
    # Create a new client and connect to the server
    client = MongoClient(uri)
    
    def __init__(self):
        self.db = self.client["humanis_face"]
        self.collection = self.db["face_test"]

    def get_face_representation(self, user_id):
        user = self.collection.find_one({"_id": user_id})
        return user["face_representation"]

    def get_user(self, user_id):
        user = self.collection.find_one({"_id": user_id})
        return user
    
    def check_if_user_exist(self, user_id):
        user = self.collection.find_one({"_id": user_id})
        if user is None:
            return False
        return True
    
    def save_face_represetaion(self, user_name, face_representation, user_id=None):
        try:
            # check if user exist
            if not self.check_if_user_exist(user_id):
                # get latest annoy indexing
                annoy_indexing = self.get_length_of_face_embedding()
                # create new user
                user = {
                    "_id": user_id,
                    "user_name": user_name,
                    "annoy_indexing": annoy_indexing + 1,
                    "face_representation": face_representation
                }
                # self.collection.insert_one(user)
                is_success = self.collection.insert_one(user).acknowledged
                if is_success:
                    return True
                else:
                    return False
            else:
                is_success = self.collection.update_one({"_id": user_id}, {"$set": {"face_representation": face_representation}}).acknowledged
                if is_success:
                    return True
                else:
                    return False
        except Exception as e:
            print(e)
            return False
            
    
    def get_length_of_face_embedding(self):
        return self.collection.count_documents({})
    
    def get_users_face_representation(self):
        users = self.collection.find({})
        # convert as list
        users = list(users)

        return users

    def get_user_from_annoy_indexing(self, annoy_indexing):
        print('Annoy indexing: ', annoy_indexing)
        user = self.collection.find_one({"annoy_indexing": annoy_indexing})
        return user

    def test_connection(self):
        try:
            self.client.admin.command('ping')
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    

