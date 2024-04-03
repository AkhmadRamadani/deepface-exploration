import os
import services.service as service
import numpy as np
from deepface.commons import distance as dst
import constant as const

class FaceRecognitionService:
    def __init__(self, mongo_face_service, voyager_service, annoy_service):
        self.mongo_face_service = mongo_face_service
        self.voyager_service = voyager_service
        self.annoy_service = annoy_service

    def registering_face_challenge(self, image, true_name, identifier=None):
        try:
            image = image
            true_name = true_name
            identifier = identifier

            if image is None:
                return (False, "empty input set passed")
            
            if identifier is None:
                identifier = true_name
            
            identifier = identifier.replace(" ", "_")

            # save image to disk uploads folder
            filename = identifier + ".jpg"
            if not os.path.exists("base_images"):
                os.makedirs("base_images")
            
            if os.path.exists(os.path.join("base_images", filename)):
                os.remove(os.path.join("base_images", filename))
            
            image.save(os.path.join("base_images", filename))

            model_name = const.face_model
            detector_backend = const.face_detector
            enforce_detection = True
            align = True

            represent_image = service.represent(
                img_path= os.path.join("base_images", filename),
                model_name=model_name,
                detector_backend=detector_backend,
                enforce_detection=enforce_detection,
                align=align,
            )

            self.mongo_face_service.save_face_represetaion(true_name, represent_image["results"][0], user_id=identifier)

            os.remove(os.path.join("base_images", filename))

            return (True, "success")
        except Exception as e:
            print(e)
            return (False, str(e))
        
    def recognize_face_challenge(self, image_path, actions=[]):
        represent_image = service.represent(
            img_path=image_path,
            model_name=const.face_model,
            detector_backend=const.face_detector,
            enforce_detection=True,
            align=True,
        ) 

        embedding_image = represent_image["results"][0]['embedding']
        copy_embedding_image = embedding_image.copy()

        # users = self.annoy_service.get_nns_by_vector(embedding_image, 8)
        embedding_image = np.array(embedding_image, dtype='f')
        embedding_image = np.expand_dims(embedding_image, axis=0)
        users = self.voyager_service.get_nns_by_vector(embedding_image, 8)

        del represent_image
        del embedding_image
        del copy_embedding_image
        os.remove(image_path)

        if users is None:
            return (False, "No user found")
        else:
            distance = users['annoy_distance']

            threshold = dst.findThreshold(const.face_model, const.threshold_mode)
            
            json_result = {
                "verified": False, 
                "user": users,
            }

            if distance <= threshold:
                json_result["verified"] = True
                return (True, json_result)
            else:
                return (True, json_result)
            
    def verify_face_challenge(self, image, identifier):
        try:
            image = image
            identifier = identifier

            if image is None:
                return (False, "empty input set passed")
            
            if identifier is None:
                return (False, "identifier is required")
            
            identifier = identifier.replace(" ", "_")

            # save image to disk uploads folder
            filename = identifier + ".jpg"
            if not os.path.exists("base_images"):
                os.makedirs("base_images")
            
            if os.path.exists(os.path.join("base_images", filename)):
                os.remove(os.path.join("base_images", filename))
            
            image.save(os.path.join("base_images", filename))

            model_name = const.face_model
            detector_backend = const.face_detector
            enforce_detection = True
            align = True

            represent_image = service.represent(
                img_path= os.path.join("base_images", filename),
                model_name=model_name,
                detector_backend=detector_backend,
                enforce_detection=enforce_detection,
                align=align,
            )

            user = self.mongo_face_service.get_face_representation(identifier)
            if user is None:
                os.remove(os.path.join("base_images", filename))
                return (False, "User not found")
            
            represent_image = represent_image["results"][0]
            embedding_image = represent_image['embedding']

            distance = dst.findCosineDistance(embedding_image, user['embedding'])

            threshold = dst.findThreshold(const.face_model, const.threshold_mode)

            json_result = {
                "verified": False, 
                "distance": distance,
            }

            if distance <= threshold:
                json_result["verified"] = True
                os.remove(os.path.join("base_images", filename))
                return (True, json_result)
            else:
                os.remove(os.path.join("base_images", filename))
                return (False, json_result)
        except Exception as e:
            return (False, str(e))

        

