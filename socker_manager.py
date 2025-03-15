import json
import threading
import time
from decimal import Decimal, ROUND_DOWN

import websocket
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from database.connection import Connection
from tradingbinance.Binaceapi import BinanceApi

app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

socket_thread: threading.Thread = None
stop_event = threading.Event()

def connect_to_websocket_server(email, password, binance_key, binance_secret, type):
    global stop_event
    uri = "ws://45.80.181.3:8001/ws"

    while not stop_event.is_set():
        try:
            ws = websocket.WebSocket()
            ws.connect(uri)
            ws.settimeout(1)

            credentials_message = f"email={email}&password={password}"
            ws.send(credentials_message)

            while not stop_event.is_set():
                try:
                    message = ws.recv()
                    if not message:
                        continue
                except websocket.WebSocketTimeoutException:
                    continue

                try:
                    data = json.loads(message)
                    if isinstance(data, dict) and 'Symbol' in data:
                        cursor = Connection.get_cursor()
                        cursor.execute("SELECT * FROM keyCollection WHERE email = ?", (email,))
                        col = cursor.fetchone()

                        if not col:
                            print(f"No key found for email: {email}")
                            continue

                        binance_api = BinanceApi(api_key=binance_key, api_secret=binance_secret)
                        coin_price = binance_api.get_future_price(data['Symbol'])

                        amount = col[5]
                        amount = int(amount) / float(coin_price)

                        quantity = adjust_quantity(data['Symbol'], amount, binance_api)
                        data['Quantity'] = float(quantity)
                        coin_price = binance_api.get_future_price(data['Symbol'])
                        data['Price'] = coin_price
                        data['order_type'] = type
                        data['email'] = email
                        if type == 'future':
                            binance_api.create_order_future(data)
                        else:
                            binance_api.create_order_spot(data)
                except json.JSONDecodeError:
                    print(f"📩 error {message}")
                except Exception as e:
                    print(e)
                    time.sleep(5)
        except Exception as e:
            if stop_event.is_set():
                break
            print(f"Cannot connect to socket: {e}")
            time.sleep(5)

def adjust_quantity(symbol, quantity, binance):
    exchange_info = binance.futures_exchange_info(symbol)
    for symbol_info in exchange_info['symbols']:
        if symbol_info['symbol'] == symbol:
            step_size = Decimal(symbol_info['filters'][1]['stepSize'])
            return Decimal(quantity).quantize(
                step_size, rounding=ROUND_DOWN
            )
    return quantity

def start_local_socket_thread(email, password, binance_key, binance_secret, type):
    global socket_thread, stop_event

    if socket_thread is not None and socket_thread.is_alive():
        stop_event.set()
        socket_thread.join()

    stop_event.clear()

    socket_thread = threading.Thread(target=connect_to_websocket_server, args=(email, password, binance_key, binance_secret, type))
    socket_thread.daemon = True
    socket_thread.start()