from dotenv import load_dotenv
import os
load_dotenv()

mongo_uri = os.environ.get('DATABASE_URL')
face_model = 'Facenet512'
face_detector = 'opencv'
threshold_mode = 'cosine'
secret_key = os.environ.get("JWT_SECRET_KEY")
fernet_key = os.environ.get("FERNET_KEY")