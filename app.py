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

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from controllers.KeyController import KeyController
from controllers.AuthController import AuthController
from controllers import ReportController
from database.connection import Connection, key_col
from services.bot import run_scrapper

def start_mongodb():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mongodb_path = os.path.join(current_dir, "mongodb", "bin", "mongod.exe")
        print(f"Путь к MongoDB: {mongodb_path}")
        db_path = os.path.join(current_dir, "mongodb", "data")

        if not os.path.exists(db_path):
            os.makedirs(db_path)

        process = subprocess.Popen([mongodb_path, "--dbpath", db_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        return process
    except Exception as e:
        return None

mongo_process = start_mongodb()

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
            entry['Time'] = datetime.strptime(entry['Time'], '%H:%M:%S')
        except ValueError:
            entry['Time'] = None
    sorted_data = sorted(data_array, key=lambda x: x['Time'] or datetime.min, reverse=True)
    return sorted_data

def fetch_logs():
    try:
        logs_col = Connection.get_logs_col()
        result = logs_col.find()
        data_array = []
        for doc in result:
            doc['_id'] = str(doc['_id'])
            data_array.append(doc)
        return data_array
    except Exception as e:
        print(f"Ошибка получения логов: {e}")
        return []

def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Тип {type(obj)} не сериализуется")

def send_periodic_data():
    while True:
        data_array = fetch_logs()
        if data_array:
            serialized_data = json.loads(json.dumps(data_array, default=serialize_datetime))
            socketio.emit('data', {'message': 'Data retrieved', 'data': serialized_data})
        time.sleep(1)

def start_data_thread():
    thread = threading.Thread(target=send_periodic_data)
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
                     user_data['trading_view_chart_link'])
    except Exception as e:
        print(f"Ошибка в боте: {e}")

@socketio.on('connect')
def on_connect():
    print("Клиент подключился, запускаем поток передачи данных.")
    start_data_thread()

def run_flask_and_socketio():
    socketio.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_flask_and_socketio()
