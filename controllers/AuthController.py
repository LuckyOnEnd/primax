import jwt
import datetime

import requests
from flask import request, jsonify
from marshmallow import ValidationError

from auth.decorator import SECRET_KEY
from database.connection import user_col, key_col
from services.bot import run_scrapper
from socker_manager import start_local_socket_thread
from validators.auth.authSchema import AuthSchema


class AuthController:
    @classmethod
    def auth(cls):
        try:
            if request.method != 'POST':
                return jsonify({'message': 'Such method not allowed', 'success': False}), 405

            data = request.json

            try:
                validate_data = AuthSchema().load(data)
                response = requests.post(
                    f'http://127.0.0.1:8001/auth?username='
                    f'{data['user_id']}&password={data['password']}')
                response.raise_for_status()
                token = response.json()

                existing_doc = user_col.find_one(
                    {"email": validate_data["user_id"]}
                )

                if not existing_doc:
                    user_col.insert_one(
                        {
                            'password': data['password'],
                            'email': validate_data["user_id"]
                        }
                    )

                    existing_doc = user_col.find_one(
                        {"email": validate_data["user_id"]}
                    )
                    key_col.insert_one({
                        'email': validate_data["user_id"],
                        'subscription_type': token['data']['subscription_type'],
                        'type': 'future',
                        'trading_view_chart_link': '',
                        'trading_view_login': '',
                        'trading_view_password': ''
                    })

                if existing_doc.get('subscription_type') != token['data']['subscription_type']:
                    key_col.update_one(
                        {'email': validate_data["user_id"]},
                        {'$set': {'subscription_type': token['data']['subscription_type']}}
                    )

                token_jwt = jwt.encode(
                    {
                        "user_id": validate_data["user_id"],
                        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
                    },
                    SECRET_KEY,
                    algorithm="HS256"
                )

                if not token:
                    raise Exception('User not found')

                keys_data = key_col.find_one({'email': existing_doc['email']})
                binance_api = keys_data.get('api_key')
                binance_sec = keys_data.get('api_sec')

                if token['data']['subscription_type'] == 'essential':
                    if binance_api and binance_sec:
                        start_local_socket_thread(
                            validate_data['user_id'],
                            validate_data['password'],
                            binance_api,
                            binance_sec,
                            keys_data.get('type', None),
                        )
                elif token['data']['subscription_type'] == 'premium':
                    run_scrapper(keys_data['trading_view_login'], keys_data[
                        'trading_view_password'], keys_data['trading_view_chart_link'])

                return jsonify(
                    {
                        'message': 'Authenticated successfully',
                        'token': token_jwt,
                        'subscription_type': token['data']['subscription_type'],
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
