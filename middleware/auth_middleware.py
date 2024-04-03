from functools import wraps
import jwt
from flask import request, abort
from flask import current_app
from data_models.user_model import User 
import constant as const
from cryptography.fernet import Fernet

fernet = Fernet(const.fernet_key)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "e-face-api-key" in request.headers:
            splitted = request.headers["e-face-api-key"]
            try:
                token = fernet.decrypt(splitted.encode()).decode()
            except Exception as e:
                return {
                    "message": "Invalid Authentication token!",
                    "status_code": 401,
                    "result": "Unauthorized"
                }, 401


        if not token:
            return {
                "message": "Authentication Token is missing!",
                "status_code": 401,
                "result": "Unauthorized"
            }, 401
        try:
            data=jwt.decode(token, const.secret_key, algorithms=["HS256"])
            current_user = User().get_by_id(data["user_id"])
            if current_user is None:
                return {
                "message": "Invalid Authentication token!",
                "status_code": 401,
                "result": "Unauthorized"
            }, 401
            if not current_user["active"]:
                abort(403)
        except Exception as e:
            return {
                "message": "Something went wrong",
                "status_code": 401,
                "result": str(e)
            }, 500

        return f(current_user, *args, **kwargs)

    return decorated