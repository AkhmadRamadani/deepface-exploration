from flask import Flask
from routes import blueprint
from pymongo import MongoClient
import constant as const

def create_app():
    app = Flask(__name__)
    client = MongoClient(const.mongo_uri)
    db = client["face_recognition"]
    app.db = db
    app.register_blueprint(blueprint)
    return app
