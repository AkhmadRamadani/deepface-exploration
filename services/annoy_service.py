from annoy import AnnoyIndex

class AnnoyService:
    def __init__(self, mongo_service):
        self.index = None
        self.mongo = mongo_service

    def build_index(self):
        self.index = AnnoyIndex(512, 'angular')
        users = self.mongo.get_users_face_representation()
        for user in users:
            face_representation = user['face_representation']
            face_embedding = face_representation['embedding']
            annoy_indexing = user['annoy_indexing']
            self.index.add_item(annoy_indexing, face_embedding)
        self.index.build(10)
        self.index.save('model_index/annoy_index.ann')
    
    def read_index(self):
        self.index = AnnoyIndex(512, 'angular')
        self.index.load('model_index/annoy_index.ann')

    def get_nns_by_vector(self, vector, n):
        if self.index == None:
            self.read_index()
        neighbors, distances = self.index.get_nns_by_vector(vector, n, include_distances=True)

        if len(neighbors) > 0:
            neighbor = neighbors[0]
            user = self.mongo.get_user_from_annoy_indexing(neighbor)
            user['annoy_distance'] = distances[0]
            del user['face_representation']
            return user
        else:
            return None
        
    def get_nns_by_item(self, item, n):
        if self.index == None:
            self.read_index()
        neighbors = self.index.get_nns_by_item(item, n)
        if len(neighbors) > 0:
            neighbor = neighbors[0]
            user = self.mongo.get_user_from_annoy_indexing(neighbor)
            user['annoy_distance'] = 0
            del user['face_representation']
            return user
        else:
            return None
        
    def get_item_vector(self, item):
        if self.index == None:
            self.read_index()
        vector = self.index.get_item_vector(item)
        return vector
    
    def get_n_items(self):
        if self.index == None:
            self.read_index()
        return self.index.get_n_items()
    
    def get_n_trees(self):
        if self.index == None:
            self.read_index()
        return self.index.get_n_trees()
