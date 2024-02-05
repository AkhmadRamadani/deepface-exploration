from flask import Blueprint, request
import services.service as service
import os
import datetime
from deepface.commons import distance as dst
from services.mongo_service import MongoService
from services.voyager_service import VoyagerService
import numpy as np


blueprint = Blueprint("routes", __name__)
mongo = MongoService()
voyager_service = VoyagerService(mongo_service=mongo)

face_model = 'Facenet512'
face_detector = 'opencv'
threshold_mode = 'cosine'

@blueprint.route("/")
def home():
    return "<h1>Welcome to Deep Face Exploration API</h1>"

@blueprint.route("/registering_face", methods=["POST"])
def registering_face():
    image = request.files.get("image")
    identifier = request.form.get("identifier")
    if image is None or identifier is None:
        return {"status_code": 400, "message": "error", "result": "empty input set passed"}
    
    result = registering_face_challenge(image, identifier)

    if result[0]:
        return {"status_code": 200, "message": "success"}
    else:
        return {"status_code": 400, "message": result[1]}


def registering_face_challenge(image, true_name):
    try:
        image = image
        true_name = true_name

        if image is None:
            return (False, "empty input set passed")

        # save image to disk uploads folder
        filename = true_name.replace(" ", "_") + ".jpg"
        if not os.path.exists("base_images"):
            os.makedirs("base_images")
        
        if os.path.exists(os.path.join("base_images", filename)):
            os.remove(os.path.join("base_images", filename))
        
        image.save(os.path.join("base_images", filename))

        model_name = face_model
        detector_backend = face_detector
        enforce_detection = False
        align = True

        represent_image = service.represent(
            img_path= os.path.join("base_images", filename),
            model_name=model_name,
            detector_backend=detector_backend,
            enforce_detection=enforce_detection,
            align=align,
        )

        mongo.save_face_represetaion(true_name, represent_image["results"][0], user_id=true_name.replace(" ", ""))

        # delete file
        os.remove(os.path.join("base_images", filename))

        return (True, "success")
    except Exception as e:
        return (False, str(e))

@blueprint.route("/face_recognition", methods=["POST"])
def face_recognition():
    analyze = request.form.get("analyze")

    if analyze == "true":
        analyze = True
    else:
        analyze = False

    embedding_image = request.files.get("image")
    
    if embedding_image is None:
        return {"status_code": 400, "message": "error", "result": "empty input set passed"}
    

    filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".jpg"
    embedding_image.save(os.path.join("uploads", filename))

    represent_image = service.represent(
        img_path=os.path.join("uploads", filename),
        model_name=face_model,
        detector_backend=face_detector,
        enforce_detection=False,
        align=True,
    ) 

    if analyze == True:
        analyze_result = service.analyze(
            img_path=os.path.join("uploads", filename),
            detector_backend=face_detector,
            enforce_detection=False,
            align=True,
            actions=["age", "gender", "emotion", "race"]
        )

    # get first element of list
    represent_image = represent_image["results"][0]
    embedding_image = represent_image['embedding']

    copy_embedding_image = embedding_image.copy()
    embedding_image = np.array(embedding_image, dtype='f')
    embedding_image = np.expand_dims(embedding_image, axis=0)
    users = voyager_service.get_nns_by_vector(embedding_image, 8)

    if users == None:
        del represent_image
        del embedding_image
        del copy_embedding_image

        # delete file
        os.remove(os.path.join("uploads", filename))

        return {"status_code": 200, "message": "success", "result": "no user found"}
    else:
        # distance between two embeddings
        distance = users["annoy_distance"]
        
        threshold = dst.findThreshold(face_model, threshold_mode)

        del represent_image
        del embedding_image
        del copy_embedding_image

        # delete file
        os.remove(os.path.join("uploads", filename))
        json_result = {
                    "status_code": 200, 
                    "message": "success", 
                    "result": 
                        {
                            "verified": False, 
                            "user": users,
                        }
                    }
        if analyze == True:
            json_result["result"]["analyze"] = analyze_result["results"][0]

        if distance <= threshold:
            json_result["result"]["verified"] = True
            return json_result
        else:
            return json_result
        
@blueprint.route("/face_verification", methods=["POST"])
def face_verification():
    
    identifier = request.form.get("identifier")
    embedding_image = request.files.get("image")
    analyze = request.form.get("analyze")

    if embedding_image is None:
        return {"status_code": 400, "message": "error", "result": "empty input set passed"}
    if identifier is None:
        return {"status_code": 400, "message": "error", "result": "empty input set passed"}
    if analyze == "true":
        analyze = True
    else:
        analyze = False
    
    filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".jpg"
    embedding_image.save(os.path.join("uploads", filename))

    represent_image = service.represent(
        img_path=os.path.join("uploads", filename),
        model_name=face_model,
        detector_backend=face_detector,
        enforce_detection=False,
        align=True,
    )

    # get first element of list
    represent_image = represent_image["results"][0]
    embedding_image = represent_image['embedding']

    # get user saved embedding
    represent_file = mongo.get_user(identifier)
    # get embedding
    embedding_base = represent_file["face_representation"]["embedding"]
    # distance between two embeddings
    distance = 0.0
    if threshold_mode == 'cosine':
        distance = dst.findCosineDistance(embedding_image, embedding_base)
    else:
        distance = dst.findEuclideanDistance(embedding_image, embedding_base)

    threshold = dst.findThreshold(face_model, threshold_mode)

    del represent_image
    del embedding_image
    del represent_file['face_representation']

    # delete file
    os.remove(os.path.join("uploads", filename))

    if distance <= threshold:
        return {
                "status_code": 200, 
                "message": "success", 
                "result": 
                    {
                        "verified": True, 
                        "distance": distance, 
                        "threshold": threshold, 
                        "user": represent_file
                    }
                
                }
    else:
        return {
                "status_code": 200, 
                "message": "success", 
                "result": 
                    {
                        "verified": False, 
                        "distance": distance,
                        "threshold": threshold, 
                        "user": represent_file
                    }
                
                }
    
    

@blueprint.route("/test_connection", methods=["GET"])
def test_connection():
    return mongo.test_connection()


@blueprint.route("/rebuild_voyager", methods=["GET"])
def voyager_test():
    voyager_service.build_index()
    return {"status_code": 200, "message": "success", "result": "oke"}


@blueprint.route("/find_face_voyager", methods=["POST"])
def voyager_find_face():
    embedding_image = request.form["embedding_image"]
    # remove [ and ] from string
    embedding_image = embedding_image.replace("[", "").replace("]", "")

    # split by comma and make it a list
    embedding_image = embedding_image.split(",")

    # convert string to float
    embedding_image = [float(i) for i in embedding_image]
    copy_embedding_image = embedding_image.copy()
    embedding_image = np.array(embedding_image, dtype='f')
    embedding_image = np.expand_dims(embedding_image, axis=0)
    users = voyager_service.get_nns_by_vector(embedding_image, 1)
    if users == None:
        return {"status_code": 200, "message": "success", "result": "no user found"}
    else:
        represent_file = mongo.get_face_representation(users["_id"])
        # get embedding
        embedding_base = represent_file["embedding"]
        # distance between two embeddings
        distance = 0.0
        if threshold_mode == 'cosine':
            distance = dst.findCosineDistance(copy_embedding_image, embedding_base)
        else:
            distance = dst.findEuclideanDistance(copy_embedding_image, embedding_base)
        
        threshold = dst.findThreshold(face_model, threshold_mode)

        if distance <= threshold:
            return {
                    "status_code": 200, 
                    "message": "success", 
                    "result": 
                        {
                            "verified": True, 
                            "distance": distance, 
                            "threshold": threshold, 
                            "user_name": users["user_name"], 
                            "annoy_user": users
                        }
                    
                    }
        else:
            return {
                    "status_code": 200, 
                    "message": "success", 
                    "result": 
                        {
                            "verified": False, 
                            "distance": distance,
                            "threshold": threshold, 
                            "user_name": users["user_name"], 
                            "annoy_user": users
                        }
                    
                    }
    