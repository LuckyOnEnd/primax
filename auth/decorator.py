from flask import request

import jwt
from functools import wraps
from flask import request, jsonify
from database.connection import user_col
from bson import ObjectId

SECRET_KEY = "your_secret_key"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing!', 'success': False}), 401

        try:
            token = token.split("Bearer ")[-1]
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = user_col.find_one({"email": data["user_id"]})
            if not current_user:
                return jsonify({'message': 'User not found', 'success': False}), 401

            return f(*args, **kwargs, current_user=current_user)

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired', 'success': False}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token', 'success': False}), 401
        except Exception as e:
            print(f'Authorization failed {e}')

    return decorated