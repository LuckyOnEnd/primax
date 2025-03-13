import jwt
from functools import wraps
from flask import request, jsonify
from database.connection import Connection

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

            # Используем SQLite вместо MongoDB
            cursor = Connection.get_cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (data["user_id"],))
            current_user = cursor.fetchone()

            if not current_user:
                return jsonify({'message': 'User not found', 'success': False}), 401

            # Преобразуем результат в словарь для совместимости с предыдущим кодом
            current_user_dict = {
                "email": current_user[0],  # Предполагаем, что email - первый столбец
                "password": current_user[1]  # Предполагаем, что password - второй столбец
            }

            return f(*args, **kwargs, current_user=current_user_dict)

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired', 'success': False}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token', 'success': False}), 401
        except Exception as e:
            print(f'Authorization failed: {e}')
            return jsonify({'message': 'Authorization failed', 'success': False}), 500

    return decorated