import jwt
import datetime
import requests
from flask import request, jsonify
from marshmallow import ValidationError

from auth.decorator import SECRET_KEY
from database.connection import Connection
from services.bot import run_scrapper
from socker_manager import start_local_socket_thread
from validators.auth.authSchema import AuthSchema
import urllib.parse
from socker_manager import start_public_socket_thread
from auth.decorator import session
class AuthController:
    @classmethod
    def auth(cls):
        try:
            print('Authorize ...')
            if request.method != 'POST':
                return jsonify({'message': 'Such method not allowed', 'success': False}), 405

            data = request.json

            try:
                validate_data = AuthSchema().load(data)
                password_encoded = urllib.parse.quote(data["password"])
                response = requests.post(
                    f'https://api.primexalgo.com/auth?username='
                    f'{data["user_id"]}&password={password_encoded}'
                )
                response.raise_for_status()
                token = response.json()

                conn = Connection.get_connection()
                cursor = Connection.get_cursor()

                cursor.execute("SELECT * FROM users WHERE email = ?", (validate_data["user_id"],))
                existing_doc = cursor.fetchone()

                if not existing_doc:
                    cursor.execute(
                        """
                        INSERT INTO users (password, email)
                        VALUES (?, ?)
                    """, (data['password'], validate_data["user_id"])
                        )

                    cursor.execute(
                        """
                        INSERT INTO keyCollection (
                            email, subscription_type, order_type, 
                            trading_view_chart_link, trading_view_login, trading_view_password
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                            validate_data["user_id"],
                            token['data']['subscription_type'],
                            'future',
                            '',
                            '',
                            ''
                        )
                        )
                    conn.commit()

                    cursor.execute(
                        "SELECT * FROM users WHERE email = ?", (validate_data["user_id"],)
                        )
                    existing_doc = cursor.fetchone()

                cursor.execute(
                    "SELECT subscription_type FROM keyCollection WHERE email = ?",
                    (validate_data["user_id"],)
                    )
                current_sub = cursor.fetchone()

                if current_sub and current_sub[0] != token['data']['subscription_type']:
                    cursor.execute(
                        """
                        UPDATE keyCollection 
                        SET subscription_type = ? 
                        WHERE email = ?
                    """, (token['data']['subscription_type'], validate_data["user_id"])
                        )
                    conn.commit()

                token_jwt = jwt.encode(
                    {
                        "user_id": validate_data["user_id"],
                        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2),
                        "session": str(session)
                    },
                    SECRET_KEY,
                    algorithm="HS256"
                )

                if not token:
                    raise Exception('User not found')

                cursor.execute(
                    "SELECT * FROM keyCollection WHERE email = ?",
                    (validate_data["user_id"],)
                    )
                keys_data = cursor.fetchone()


                binance_api = keys_data[1] if keys_data else None
                binance_sec = keys_data[2] if keys_data else None

                if binance_api and binance_sec:
                    start_local_socket_thread(
                        validate_data['user_id'],
                        validate_data['password'],
                        binance_api,
                        binance_sec,
                        keys_data[3] if keys_data else None,
                    )
                elif token['data']['subscription_type'] == 'premium':
                    try:
                        run_scrapper(keys_data['trading_view_login'], keys_data[
                            'trading_view_password'], keys_data['trading_view_chart_link'], validate_data['user_id'])
                    except Exception as e:
                        print(f"Error while running scrapper: {e}")

                start_public_socket_thread(
                    validate_data['user_id'],
                )

                print('Authorized')
                return jsonify(
                    {
                        'message': 'Authenticated successfully',
                        'token': token_jwt,
                        'subscription_type': token['data']['subscription_type'],
                        'success': True
                    }
                ), 200

            except ValidationError as error:
                print(f'Validation error {error}')
                return jsonify(
                    {
                        'message': 'Validation error',
                        'error': error.messages,
                        'success': False
                    }
                ), 400

        except Exception as e:
            print(f'Error while authorizing:{e}')
            return jsonify(
                {
                    'message': 'Internal server error',
                    'error': str(e),
                    'success': False
                }
            ), 500