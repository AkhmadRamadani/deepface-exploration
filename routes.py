from flask import Blueprint, request
import os, jwt
import datetime
from services.mongo.mongo_service import MongoFaceService
from services.mongo.auth_service import AuthService
from services.voyager_service import VoyagerService
from services.annoy_service import AnnoyService
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import pandas as pd
from pymongo import MongoClient
import constant as const 
from services.face_recognition.face_recognition_service import FaceRecognitionService
from validator import validate_email
from data_models.user_model import User
from middleware.auth_middleware import token_required
from middleware.api_request_call_middleware import log_api_request_call_middleware
from cryptography.fernet import Fernet
import time
import json
import math

blueprint = Blueprint("routes", __name__)

# define service
mongo_client = MongoClient(const.mongo_uri)
mongo_face_service = MongoFaceService(mongo_client)
voyager_service = VoyagerService(mongo_service=mongo_face_service)
annoy_service = AnnoyService(mongo_service=mongo_face_service)

# user service
user_service = AuthService(mongo_client)

# face_recognition service
fr_service = FaceRecognitionService(
    mongo_face_service=mongo_face_service,
    voyager_service=voyager_service,
    annoy_service=annoy_service,
)

f = Fernet(const.fernet_key)

@blueprint.route("/")
def home():
    return "<h1>Welcome to E-Face API</h1>"

@blueprint.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")

    if name is None or email is None or password is None:
        return {"status_code": 400, "message": "error", "result": "empty input set passed"}
    
    is_email_valid = validate_email(email)

    if not is_email_valid:
        return {"status_code": 400, "message": "error", "result": "invalid email format"}
    
    user = User().create(name, email, password, role)

    if user is None:
        return {"status_code": 400, "message": "error", "result": "user already exist"}, 400
    else:
        return {"status_code": 200, "message": "success", "result": user}, 200

@blueprint.route("/generate_token", methods=["POST"])
def generate_token():
    email = request.form.get("email")
    password = request.form.get("password")

    if email is None or password is None:
        return {"status_code": 400, "message": "error", "result": "empty input set passed"}
    
    is_email_valid = validate_email(email)
    
    if not is_email_valid:
        return {"status_code": 400, "message": "error", "result": "invalid email format"}
    
    user = User().login(email, password)

    if user is None:
        return {"status_code": 400, "message": "error", "result": "invalid email or password"}
    
    else:
        try:
            token = jwt.encode(
                {
                    "user_id": str(user["_id"]),
                },
                const.secret_key,
                algorithm="HS256"
            )

            token = f.encrypt(bytes(token, "utf-8")).decode()

            user["token"] = token

            user["_id"] = str(user["_id"])
            return {"status_code": 200, "message": "success", "result": user}
        except Exception as e:
            return {"status_code": 500, "message": "error", "result": str(e)}
    

@blueprint.route("/face_registration", methods=["POST"])
@token_required
def registering_face(current_user):
    image = request.files.get("image")
    identifier = request.form.get("identifier")
    real_name = request.form.get("real_name")
    
    if image is None or real_name is None:
        return {"status_code": 400, "message": "error", "result": "empty input set passed"}, 400
    
    result = fr_service.registering_face_challenge(image, real_name, identifier=identifier)

    if result[0]:
        return {"status_code": 200, "message": "success"}, 200
    else:
        return {"status_code": 200, "message": result[1]}, 200
    

@blueprint.route("/face_verification", methods=["POST"])
@token_required
def face_verification(current_user):
    identifier = request.form.get("identifier")
    image = request.files.get("image")

    if image is None or identifier is None:
        return {"status_code": 400, "message": "error", "result": "empty input set passed"}, 400
    
    result = fr_service.verify_face_challenge(image, identifier)

    if result[0]:
        return {"status_code": 200, "message": "success", "result": result[1]}, 200
    else:
        return {"status_code": 200, "message": result[1]}, 200


@blueprint.route("/face_recognition", methods=["POST"])
@token_required
def face_recognition(current_user):
    embedding_image = request.files.get("image")
    
    if embedding_image is None:
        return {"status_code": 400, "message": "error", "result": "empty input set passed"}, 400
    

    filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".jpg"
    filename_at_upload = os.path.join("uploads", filename)
    embedding_image.save(filename_at_upload)

    result = fr_service.recognize_face_challenge(image_path=filename_at_upload)

    if result[0]:
        return {"status_code": 200, "message": "success", "result": result[1]}, 200
    else:
        return {"status_code": 200, "message": result[1]}, 200


# # register multiple face using csv file
@blueprint.route("/multiple_face_registration", methods=["POST"])
@token_required
def multiple_face_registration(current_user):
    excel_file = request.files.get("excel_file")
    if excel_file is None:
        return {"status_code": 400, "message": "error", "result": "empty input set passed"}
    
    filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".xlsx"
    excel_file.save(os.path.join("uploads", filename))

    df = pd.read_excel(os.path.join("uploads", filename))
    list_of_error_data = []
    for index, row in df.iterrows():
        try:
            if row["photo"] is None or row["name"] is None:
                list_of_error_data.append(row)
                continue
            
            # check if photo is url or not
            # if yes then download the image
            # if no then check from local
            if "http" not in row["photo"]:
                if not os.path.exists(row["photo"]):
                    list_of_error_data.append(row)
                    continue
                else:
                    img = Image.open(row["photo"]).convert("RGB")
                    img.save(os.path.join("uploads", row["name"] + ".jpg"))
                    # set new identifier from name and id
                    identifier_new = row["name"] + "_" + str(row["id"])
                    result = fr_service.registering_face_challenge(img, row["name"], identifier=identifier_new)
                    if result[0]:
                        print("Success")
                    else:
                        list_of_error_data.append(row)
                        print("Failed")
            else:
                image = requests.get(row["photo"])
                img = Image.open(BytesIO(image.content)).convert("RGB")
                img.save(os.path.join("uploads", row["name"] + ".jpg"))
                result = fr_service.registering_face_challenge(img, row["name"], identifier=row["id"])
                if result[0]:
                    print("Success")
                else:
                    print("Failed")
            
            # delete file
            os.remove(os.path.join("uploads", row["name"] + ".jpg"))


        except Exception as e:
            print(str(e))
            # add reason to list of error data
            row["reason"] = str(e)
            list_of_error_data.append(row)
            continue
    
    os.remove(os.path.join("uploads", filename))
    
    if len(list_of_error_data) > 0:
        # save as csv file
        df = pd.DataFrame(list_of_error_data)
        error_csv_name = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".csv"
        # save it to folder error_list_bulk_import
        df.to_csv(os.path.join("error_list_bulk_import", error_csv_name), index=False)

        return {"status_code": 200, "message": "success", "result": "some data failed to register, check the csv file", "csv_file": error_csv_name}

    return {"status_code": 200, "message": "success", "result": "all data registered successfully"}


@blueprint.route("/test_log", methods=["GET"])
@log_api_request_call_middleware
def test_log():
    # get from url params i
    i = request.args.get("i")
    
    for j in range(int(i)):
        if (j == 1 or j == i):
            print(j)
    
    # delay for 5 seconds
    time.sleep(5)

    return {"status_code": 200, "message": "success", "result": "oke"}

@blueprint.route("/get_log", methods=["GET"])
def get_log():
    limit = request.args.get("limit")
    page = request.args.get("page")
    filterParams = request.args.get("filter")

    if limit is None:
        limit = 10
    if page is None:
        page = 1

    if limit is not None:
        limit = int(limit)
    if page is not None:
        page = int(page)

    logs = []
    logs_copy = []
    with open(os.path.join("logs", "api_request_call.json"), "r") as logg:
        logs = json.load(logg)
        logs_copy = logs.copy()

    if filterParams is not None:
        filterParams = filterParams.lower()
        logs = [log for log in logs if (filterParams in log["endpoint"].lower() or filterParams in log["method"].lower())]
    
    total_data = len(logs)
    

    logs = logs[(int(page) - 1) * int(limit):int(page) * int(limit)]


    meta = {
        "total_data": total_data,
        "total_page": math.ceil(total_data / limit),
    }

    result = {
        "meta": meta,
        "data": logs
    }
    
    return {"status_code": 200, "message": "success", "data": result}


# @blueprint.route("/face_recognition_annoy", methods=["POST"])
# def face_recognition_annoy():
#     analyze = request.form.get("analyze")

#     if analyze == "true":
#         analyze = True
#     else:
#         analyze = False

#     embedding_image = request.files.get("image")
    
#     if embedding_image is None:
#         return {"status_code": 400, "message": "error", "result": "empty input set passed"}
    

#     filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".jpg"
#     embedding_image.save(os.path.join("uploads", filename))

#     represent_image = service.represent(
#         img_path=os.path.join("uploads", filename),
#         model_name=face_model,
#         detector_backend=face_detector,
#         enforce_detection=False,
#         align=True,
#     ) 

#     if analyze == True:
#         analyze_result = service.analyze(
#             img_path=os.path.join("uploads", filename),
#             detector_backend=face_detector,
#             enforce_detection=False,
#             align=True,
#             actions=["emotion"]
#         )

#     # get first element of list
#     represent_image = represent_image["results"][0]
#     embedding_image = represent_image['embedding']

#     copy_embedding_image = embedding_image.copy()
#     users = annoy_service.get_nns_by_vector(embedding_image, 8)

#     if users == None:
#         del represent_image
#         del embedding_image
#         del copy_embedding_image

#         # delete file
#         os.remove(os.path.join("uploads", filename))

#         return {"status_code": 200, "message": "success", "result": "no user found"}
#     else:
#         # distance between two embeddings
#         distance = users["annoy_distance"]
        
#         threshold = dst.findThreshold(face_model, threshold_mode)

#         del represent_image
#         del embedding_image
#         del copy_embedding_image

#         # delete file
#         os.remove(os.path.join("uploads", filename))
#         json_result = {
#                     "status_code": 200, 
#                     "message": "success", 
#                     "result": 
#                         {
#                             "verified": False, 
#                             "user": users,
#                         }
#                     }
#         if analyze == True:
#             json_result["result"]["analyze"] = analyze_result["results"][0]

#         if distance <= threshold:
#             json_result["result"]["verified"] = True
#             return json_result
#         else:
#             return json_result
        
        
# @blueprint.route("/face_verification", methods=["POST"])
# def face_verification():
    
#     identifier = request.form.get("identifier")
#     embedding_image = request.files.get("image")
#     analyze = request.form.get("analyze")

#     if embedding_image is None:
#         return {"status_code": 400, "message": "error", "result": "empty input set passed"}
#     if identifier is None:
#         return {"status_code": 400, "message": "error", "result": "empty input set passed"}
#     if analyze == "true":
#         analyze = True
#     else:
#         analyze = False
    
#     filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".jpg"
#     embedding_image.save(os.path.join("uploads", filename))

#     represent_image = service.represent(
#         img_path=os.path.join("uploads", filename),
#         model_name=face_model,
#         detector_backend=face_detector,
#         enforce_detection=False,
#         align=True,
#     )

#     # get first element of list
#     represent_image = represent_image["results"][0]
#     embedding_image = represent_image['embedding']

#     # get user saved embedding
#     represent_file = mongo_face_service.get_user(identifier)
#     # get embedding
#     embedding_base = represent_file["face_representation"]["embedding"]
#     # distance between two embeddings
#     distance = 0.0
#     if threshold_mode == 'cosine':
#         distance = dst.findCosineDistance(embedding_image, embedding_base)
#     else:
#         distance = dst.findEuclideanDistance(embedding_image, embedding_base)

#     threshold = dst.findThreshold(face_model, threshold_mode)

#     del represent_image
#     del embedding_image
#     del represent_file['face_representation']

#     # delete file
#     os.remove(os.path.join("uploads", filename))

#     if distance <= threshold:
#         return {
#                 "status_code": 200, 
#                 "message": "success", 
#                 "result": 
#                     {
#                         "verified": True, 
#                         "distance": distance, 
#                         "threshold": threshold, 
#                         "user": represent_file
#                     }
                
#                 }
#     else:
#         return {
#                 "status_code": 200, 
#                 "message": "success", 
#                 "result": 
#                     {
#                         "verified": False, 
#                         "distance": distance,
#                         "threshold": threshold, 
#                         "user": represent_file
#                     }
                
#                 }

# @blueprint.route("/test_connection", methods=["GET"])
# def test_connection():
#     return mongo_face_service.test_connection()


@blueprint.route("/rebuild_indexing", methods=["GET"])
def voyager_test():
    voyager_service.build_index()
    annoy_service.build_index()
    return {"status_code": 200, "message": "success", "result": "oke"}


# @blueprint.route("/find_face_voyager", methods=["POST"])
# def voyager_find_face():
#     embedding_image = request.form["embedding_image"]
#     # remove [ and ] from string
#     embedding_image = embedding_image.replace("[", "").replace("]", "")

#     # split by comma and make it a list
#     embedding_image = embedding_image.split(",")

#     # convert string to float
#     embedding_image = [float(i) for i in embedding_image]
#     copy_embedding_image = embedding_image.copy()
#     embedding_image = np.array(embedding_image, dtype='f')
#     embedding_image = np.expand_dims(embedding_image, axis=0)
#     users = voyager_service.get_nns_by_vector(embedding_image, 1)
#     if users == None:
#         return {"status_code": 200, "message": "success", "result": "no user found"}
#     else:
#         represent_file = mongo_face_service.get_face_representation(users["_id"])
#         # get embedding
#         embedding_base = represent_file["embedding"]
#         # distance between two embeddings
#         distance = 0.0
#         if threshold_mode == 'cosine':
#             distance = dst.findCosineDistance(copy_embedding_image, embedding_base)
#         else:
#             distance = dst.findEuclideanDistance(copy_embedding_image, embedding_base)
        
#         threshold = dst.findThreshold(face_model, threshold_mode)

#         if distance <= threshold:
#             return {
#                     "status_code": 200, 
#                     "message": "success", 
#                     "result": 
#                         {
#                             "verified": True, 
#                             "distance": distance, 
#                             "threshold": threshold, 
#                             "user_name": users["user_name"], 
#                             "annoy_user": users
#                         }
                    
#                     }
#         else:
#             return {
#                     "status_code": 200, 
#                     "message": "success", 
#                     "result": 
#                         {
#                             "verified": False, 
#                             "distance": distance,
#                             "threshold": threshold, 
#                             "user_name": users["user_name"], 
#                             "annoy_user": users
#                         }
                    
#                     }

    