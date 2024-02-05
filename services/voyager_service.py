
from voyager import Index, Space
from services.mongo_service import MongoService
import numpy as np


class VoyagerService:
    def __init__(self, mongo_service):
        self.index = None
        self.mongo = mongo_service

    def build_index(self):
        self.index = Index(Space.Cosine, num_dimensions=512)
        users = self.mongo.get_users_face_representation()
        for user in users:
            face_representation = user['face_representation']
            face_embedding = face_representation['embedding']
            annoy_indexing = user['annoy_indexing']
            self.index.add_item(face_embedding, annoy_indexing)
        self.index.save('model_index/voyager_index.voy')
        print('Voyager model saved')
    
    def read_index(self):
        self.index = Index.load('model_index/voyager_index.voy')
        print('Voyager model loaded')

    def get_nns_by_vector(self, vector, n):
        if self.index == None:
            self.read_index()
        neighbors, distances = self.index.query(vector, n)
        if len(neighbors) > 0:
            for i in range(len(neighbors)):
                print(neighbors[i], distances[i])
            neighbor = neighbors[0][0]
            neighbor = int(neighbor)
            user = self.mongo.get_user_from_annoy_indexing(neighbor)
            distance = distances[0][0]
            converted_distance = np.float64(distance)
            user['annoy_distance'] = converted_distance
            del user['face_representation']
            return user
        else:
            return None