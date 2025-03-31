import eventlet
eventlet.monkey_patch()
import os
import websockets.legacy
import websockets.legacy.client
import subprocess
import time
import socket
import json
import threading
from datetime import datetime
from selenium.common import exceptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import websockets.legacy
from websockets.legacy.client import WebSocketClientProtocol
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from controllers.KeyController import KeyController
from controllers.AuthController import AuthController
from controllers import ReportController
from database.connection import Connection, key_col
from services.bot import run_scrapper

app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

KeyControllers = KeyController()

@app.route('/')
def index():
    return "Flask app is running!"

@app.route('/api/postkey', methods=['POST'])
def post_key():
    return KeyControllers.Postkey()

@app.route('/api/close_positions', methods=['POST'])
def close_positions():
    return KeyControllers.close_positions()

@app.route('/api/report', methods=['POST'])
def get_report():
    return ReportController.get_by_date_range()

@app.route('/api/getkeys', methods=['GET'])
def get_key():
    return KeyControllers.get_single_key()

@app.route('/api/updatekey/<id>', methods=['PUT'])
def update_key(id):
    return KeyControllers.UpdateKey(id)

@app.route('/api/auth', methods=['POST'])
def authenticate_user():
    return AuthController.auth()


def sort_by_time(data_array):
    for entry in data_array:
        try:
            entry['timestamp'] = datetime.strptime(
                entry['timestamp'], '%Y-%m-%d %H:%M:%S'
                )
        except ValueError:
            entry['timestamp'] = None
    sorted_data = sorted(data_array, key=lambda x: x['timestamp'] or datetime.min, reverse=True)
    return sorted_data


def fetch_logs(email=None):
    try:
        cursor = Connection.get_cursor()
        if email:
            cursor.execute(
                "SELECT * FROM logs WHERE email = ? ORDER BY PositionOpened DESC", (email,)
                )
        else:
            cursor.execute("SELECT * FROM logs ORDER BY PositionOpened DESC")
        result = cursor.fetchall()

        data_array = []
        for row in result:
            data = {
                'Symbol': row[2],
                'Price': row[1],
                'Signal': row[4],
                'Quantity': row[5],
                'order_type': row[0],
                'Time': row[3],
                'PositionOpened': row[6],
                'commission': row[7],
                'realized_pnl': row[8],
                'email': row[9] if len(row) > 9 else email
            }
            data_array.append(data)

        return data_array
    except Exception as e:
        print(f"Error while getting logs: {e}")
        return []

def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Тип {type(obj)} не сериализуется")

def send_periodic_data(sid, email):
    while True:
        data_array = fetch_logs(email)
        if data_array:
            serialized_data = json.loads(json.dumps(data_array, default=serialize_datetime))
            socketio.emit('data', {'message': 'Data retrieved', 'data': serialized_data}, to=sid)
        time.sleep(1)

def start_data_thread(sid, email):
    thread = threading.Thread(target=send_periodic_data, args=(sid, email))
    thread.daemon = True
    thread.start()

def start_scrapper_thread():
    try:
        user_data = key_col.find_one({})
        if not user_data:
            return
        if (user_data.get('trading_view_login') in [None, ''] or
                user_data.get('trading_view_password') in [None, ''] or
                user_data.get('trading_view_chart_link') in [None, '']):
            return
        run_scrapper(user_data['trading_view_login'], user_data['trading_view_password'],
                     user_data['trading_view_chart_link'], user_data['email'])
    except Exception as e:
        print(f"Ошибка в боте: {e}")

@socketio.on('connect')
def on_connect():
    email = request.args.get('email')
    if email:
        print(f"Client connected: {email}, SID: {request.sid}")
        data_array = fetch_logs(email)
        if data_array:
            serialized_data = json.loads(json.dumps(data_array, default=serialize_datetime))
            socketio.emit('data', {'message': 'Initial data', 'data': serialized_data})
        start_data_thread(request.sid, email)
    else:
        print("Client connected without email")
        socketio.emit('error', {'message': 'Email is required'})


@socketio.on('join')
def on_join(data):
    email = data.get('email')
    if email:
        sid = request.sid
        join_room(email)
        print(f"Client joined room: {email}, SID: {sid}")

        start_data_thread(sid, email)
    else:
        socketio.emit('error', {'message': 'Email is required'}, to=request.sid)

def run_flask_and_socketio():
    socketio.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_flask_and_socketio()
