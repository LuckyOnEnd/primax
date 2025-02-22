import jwt
import datetime
from flask import request, jsonify
from marshmallow import ValidationError
from werkzeug.security import check_password_hash

from auth.decorator import SECRET_KEY
from database.connection import user_col
from validators.auth.authSchema import AuthSchema


class AuthController:
    @classmethod
    def auth(cls):
        try:
            if request.method != 'POST':
                return jsonify({'message': 'Such method not allowed', 'success': False}), 405  # 405 вместо 404

            data = request.json

            try:
                validate_data = AuthSchema().load(data)
                existing_doc = user_col.find_one(
                    {"user_id": int(validate_data["user_id"])}
                )

                if not existing_doc:
                    return jsonify(
                        {
                            'message': 'User not found',
                            'success': False
                        }
                    ), 401

                if not check_password_hash(existing_doc["password"], validate_data["password"]):
                    return jsonify(
                        {
                            'message': 'Invalid credentials',
                            'success': False
                        }
                    ), 401

                user_id = str(existing_doc["user_id"])

                token = jwt.encode(
                    {
                        "user_id": user_id,
                        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
                    },
                    SECRET_KEY,
                    algorithm="HS256"
                )

                return jsonify(
                    {
                        'message': 'Authenticated successfully',
                        'token': token,
                        'success': True
                    }
                ), 200

            except ValidationError as error:
                return jsonify(
                    {
                        'message': 'Validation error',
                        'error': error.messages,
                        'success': False
                    }
                ), 400

        except Exception as e:
            return jsonify(
                {
                    'message': 'Internal server error',
                    'error': str(e),
                    'success': False
                }
            ), 500
