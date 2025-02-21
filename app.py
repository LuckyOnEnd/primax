from datetime import datetime

import eventlet
eventlet.monkey_patch()
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from controllers.KeyController import KeyController
from controllers.AuthController import AuthController
from Scraper import TradingView
from config.config import Config
from database.connection import Connection
import time
import threading

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
            entry['Time'] = None  # Handle cases where time is empty or invalid

    sorted_data = sorted(data_array, key=lambda x: x['Time'] or datetime.min, reverse=True)
    return sorted_data

# Function to fetch logs from DB
def fetch_logs():
    try:
        logs_col = Connection.get_logs_col()
        result = logs_col.find()
        data_array = []
        for doc in result:
            doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
            data_array.append(doc)
        return data_array
    except Exception as e:
        print(f"Error retrieving logs: {e}")
        return []

# Function to emit data periodically
def send_periodic_data():
    while True:
        data_array = fetch_logs()
        if data_array:
            socketio.emit('data', {'message': 'Data retrieved', 'data': data_array})
        time.sleep(1)  # Emit data every second

def start_data_thread():
    thread = threading.Thread(target=send_periodic_data)
    thread.daemon = True
    thread.start()

@socketio.on('connect')
def on_connect():
    print("Client connected, starting data emission.")
    start_data_thread()

def Bot(Captcha_API, Username, password, path):
    Bot = TradingView(Captcha_API, Username, password, path)
    Bot.Login()
    Bot.openChart()

def run_flask_and_socketio():
    socketio.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=Bot, args=(Config.Captcha_API, Config.Username,
                                                    Config.password, Config.COOKIES_PATH))
    bot_thread.start()

    run_flask_and_socketio()






