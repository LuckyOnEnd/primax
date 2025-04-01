import os
import sys
from time import sleep

from auth.decorator import token_required
from database.connection import Connection
from services.bot import run_scrapper, stop_scrapper
from socker_manager import start_local_socket_thread
from tradingbinance.Binaceapi import BinanceApi

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from validators.keySchema.keyschema import keySchema
from marshmallow import ValidationError
from flask import request, jsonify

# validations
api_key_schema = keySchema()


class KeyController:

    @classmethod
    @token_required
    def close_positions(cls, current_user):
        try:
            cursor = Connection.get_cursor()
            cursor.execute("SELECT * FROM keyCollection WHERE email = ?", (current_user['email'],))
            existing_doc = cursor.fetchone()

            if not existing_doc:
                return jsonify({'message': 'Key not found', 'success': False}), 404

            binance = BinanceApi(existing_doc[1], existing_doc[2])
            binance.close_all_positions()
            return jsonify(
                {
                    'message': 'Positions closed',
                    'data': 'Ok',
                    'success': True
                }
            ), 200
        except Exception as e:
            return jsonify(
                {
                    'message': 'Error while closing positions',
                    'data': str(e),
                    'success': False
                }
            ), 200

    @classmethod
    @token_required
    def Postkey(cls, current_user):
        try:
            if request.method != 'POST':
                return jsonify({'message': 'Such method not allowed', 'success': False}), 404

            data = request.json
            need_to_restart = False

            try:
                validate_data = api_key_schema.load(data)
                cursor = Connection.get_cursor()
                cursor.execute(
                    "SELECT * FROM keyCollection WHERE email = ?", (current_user['email'],)
                    )
                existing_doc = cursor.fetchone()

                conn = Connection.get_connection()

                if existing_doc:
                    existing_doc_dict = {
                        'trading_view_login': existing_doc[6],
                        'trading_view_password': existing_doc[7],
                        'trading_view_chart_link': existing_doc[8],
                        'api_key': existing_doc[1],
                        'api_sec': existing_doc[2],
                        'order_type': existing_doc[3],
                        'email': existing_doc[4]
                    }

                    if all(
                            key in existing_doc_dict and existing_doc_dict[key] for key in
                            ['trading_view_login', 'trading_view_password',
                             'trading_view_chart_link']
                    ) and all(
                        key in data and data[key] for key in
                        ['trading_view_login', 'trading_view_password', 'trading_view_chart_link']
                    ) and (
                            existing_doc_dict['trading_view_login'] != data['trading_view_login'] or
                            existing_doc_dict['trading_view_password'] != data[
                                'trading_view_password'] or
                            existing_doc_dict['trading_view_chart_link'] != data[
                                'trading_view_chart_link']
                    ):
                        need_to_restart = True

                    # Обновление записи
                    update_query = """
                        UPDATE keyCollection 
                        SET api_key = ?, api_sec = ?, order_type = ?, amount = ?, 
                            trading_view_login = ?, trading_view_password = ?, 
                            trading_view_chart_link = ?, subscription_type = ?
                        WHERE email = ?
                    """
                    cursor.execute(
                        update_query, (
                            data.get('api_key', existing_doc[1]),
                            data.get('api_sec', existing_doc[2]),
                            data.get('order_type', existing_doc[3] if existing_doc[3] else 'future'),
                            data.get('amount', existing_doc[5]),
                            data.get('trading_view_login', existing_doc[6]),
                            data.get('trading_view_password', existing_doc[7]),
                            data.get('trading_view_chart_link', existing_doc[8]),
                            data.get('subscription_type', existing_doc[9]),
                            current_user['email']
                        )
                        )
                    conn.commit()

                    if need_to_restart:
                        stop_scrapper()
                        sleep(1)
                        run_scrapper(
                            data['trading_view_login'], data['trading_view_password'],
                            data['trading_view_chart_link'],
                            data['email'],
                            )

                    if data.get('api_key') and data.get('api_sec'):
                        start_local_socket_thread(
                            current_user['email'],
                            current_user['password'],
                            data['api_key'],
                            data['api_sec'],
                            existing_doc[3],  # type
                        )
                    return jsonify(
                        {
                            'message': 'API Key Updated',
                            'data': validate_data,
                            'success': True
                        }
                    ), 200
                else:
                    insert_query = """
                        INSERT INTO keyCollection (
                            api_key, api_sec, order_type, email, amount,
                            trading_view_login, trading_view_password, trading_view_chart_link,
                            subscription_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(
                        insert_query, (
                            data.get('api_key'),
                            data.get('api_sec'),
                            data.get('order_type'),
                            current_user['email'],
                            data.get('amount', 0),
                            data.get('trading_view_login'),
                            data.get('trading_view_password'),
                            data.get('trading_view_chart_link'),
                            data.get('subscription_type')
                        )
                        )
                    conn.commit()
                    return jsonify(
                        {
                            'message': 'API Key Added',
                            'data': validate_data,
                            'success': True
                        }
                    ), 200

            except ValidationError as error:
                print(f"Validation Error: {error}")
                return jsonify(
                    {
                        'message': 'Validation failed',
                        'error': error.messages,
                        'success': False
                    }
                ), 400

        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify(
                {
                    'message': 'Internal server error',
                    'error': str(e),
                    'success': False
                }
            ), 500

    @classmethod
    @token_required
    def get_single_key(cls, current_user):
        try:
            cursor = Connection.get_cursor()
            cursor.execute("SELECT * FROM keyCollection WHERE email = ?", (current_user['email'],))
            result = cursor.fetchone()

            if result:
                result_dict = {
                    '_id': str(result[0]),
                    'api_key': result[1],
                    'api_sec': result[2],
                    'order_type': result[3],
                    'email': result[4],
                    'amount': result[5],
                    'trading_view_login': result[6],
                    'trading_view_password': result[7],
                    'trading_view_chart_link': result[8],
                    'subscription_type': result[9]
                }
                return jsonify(
                    {'message': 'Data Retrieved', 'result': result_dict, 'success': True}
                    ), 200
            else:
                return jsonify({'message': 'No document found', 'success': False}), 404

        except Exception as e:
            return jsonify(
                {'message': 'Internal Server Error', 'error': str(e), 'success': False}
                ), 500

    @classmethod
    @token_required
    def UpdateKey(cls, _id, current_user):
        try:
            data = request.json
            if not data:
                return jsonify({'message': 'No data provided for update', 'success': False}), 400
            if not _id:
                return jsonify(
                    {'message': 'Missing _id in query parameters', 'success': False}
                    ), 400

            cursor = Connection.get_cursor()
            conn = Connection.get_connection()

            cursor.execute("SELECT * FROM keyCollection WHERE id = ?", (_id,))
            if not cursor.fetchone():
                return jsonify(
                    {'message': 'No document found with the given _id', 'success': False}
                    ), 404

            update_query = """
                UPDATE keyCollection 
                SET api_key = ?, api_sec = ?, order_type = ?, amount = ?, 
                    trading_view_login = ?, trading_view_password = ?, 
                    trading_view_chart_link = ?, subscription_type = ?
                WHERE id = ?
            """
            cursor.execute(
                update_query, (
                    data.get('api_key'),
                    data.get('api_sec'),
                    data.get('order_type'),
                    data.get('amount'),
                    data.get('trading_view_login'),
                    data.get('trading_view_password'),
                    data.get('trading_view_chart_link'),
                    data.get('subscription_type'),
                    _id
                )
                )
            conn.commit()

            return jsonify(
                {
                    'message': 'Document updated successfully',
                    'success': True
                }
            ), 200

        except Exception as e:
            return jsonify(
                {'message': 'Internal Server Error', 'error': str(e), 'success': False}
                ), 500