import bson 
import bcrypt
from pymongo import MongoClient
import os
from flask import current_app
import datetime as dt

class User:
    """User Model"""
    def __init__(self):
        self.db = current_app.db["users"]
        return

    def create(self, name="", email="", password="", role="user"):
        """Create a new user"""
        user = self.get_by_email(email)
        if user:
            return
        new_user = self.db.insert_one(
            {
                "name": name,
                "email": email,
                "password": self.encrypt_password(password),
                "role": role,
                "active": True,
                "createdAt": dt.datetime.now(),
                "updatedAt": dt.datetime.now()
            }
        )
        return self.get_by_id(new_user.inserted_id)

    def get_all(self):
        """Get all users"""
        users = self.db.find({"active": True})
        return [{**user, "_id": str(user["_id"])} for user in users]

    def get_by_id(self, user_id):
        """Get a user by id"""
        user = self.db.find_one({"_id": bson.ObjectId(user_id), "active": True})
        if not user:
            return
        user["_id"] = str(user["_id"])
        user.pop("password")
        return user

    def get_by_email(self, email):
        """Get a user by email"""
        user = self.db.find_one({"email": email, "active": True})
        if not user:
            return
        user["_id"] = str(user["_id"])
        return user

    def update(self, user_id, name=""):
        """Update a user"""
        data = {}
        if name:
            data["name"] = name
        user = self.db.update_one(
            {"_id": bson.ObjectId(user_id)},
            {
                "$set": data
            }
        )
        user = self.get_by_id(user_id)
        return user

    def delete(self, user_id):
        """Delete a user"""
        user = self.db.delete_one({"_id": bson.ObjectId(user_id)})
        user = self.get_by_id(user_id)
        return user

    def disable_account(self, user_id):
        """Disable a user account"""
        user = self.db.update_one(
            {"_id": bson.ObjectId(user_id)},
            {"$set": {"active": False}}
        )
        user = self.get_by_id(user_id)
        return user

    def encrypt_password(self, password):
        """Encrypt password"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def login(self, email, password):
        """Login a user"""
        user = self.get_by_email(email)
        if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            return
        user.pop("password")
        return user