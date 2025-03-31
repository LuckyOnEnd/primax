import json
import threading
import time
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

import websocket
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from database.connection import Connection
from tradingbinance.Binaceapi import BinanceApi
from tradingbinance.mt4 import MT4
from tradingbinance.mt5 import MT5

app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

socket_thread: threading.Thread = None
stop_event = threading.Event()

def connect_to_websocket_server(email, password, account, mt_password, server):
    global stop_event
    uri = "ws://45.80.181.3:8001/ws"
    ws = None

    while not stop_event.is_set():
        try:
            if ws is None or ws.connected is False:
                print(f"Attempting to connect to {uri}...")
                ws = websocket.WebSocket()
                ws.connect(uri)
                ws.settimeout(1)

                credentials_message = f"email={email}&password={password}"
                ws.send(credentials_message)
                print("Successfully connected and authenticated")

            while not stop_event.is_set():
                try:
                    message = ws.recv()
                    if not message:
                        continue
                except websocket.WebSocketTimeoutException:
                    continue
                except Exception as e:
                    print(f"Connection lost: {e}")
                    ws.close()
                    break

                try:
                    data = json.loads(message)
                    if isinstance(data, dict) and 'Symbol' in data:
                        cursor = Connection.get_cursor()
                        cursor.execute("SELECT * FROM keyCollection WHERE email = ?", (email,))
                        col = cursor.fetchone()

                        if not col:
                            print(f"No key found for email: {email}")
                            continue

                        mt_api = MT4()
                        data['Quantity'] = float(0.01)
                        data['Price'] = 'coin_price'
                        data['order_type'] = type
                        data['Email'] = email
                        data['Time'] = datetime.now().strftime("%H:%M:%S")
                        if data['Signal'] == 'Buy' or data['Signal'] == 'Sell':
                            mt_api.open_trade(data)
                        else:
                            mt_api.close_trade(data)
                except json.JSONDecodeError:
                    print(f"📩 error {message}")
                except Exception as e:
                    print(e)
                    time.sleep(5)

        except Exception as e:
            if stop_event.is_set():
                break
            print(f"Cannot connect to socket: {e}")
            if ws is not None:
                ws.close()
            ws = None
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

def start_local_socket_thread(email, password, account, mt_password, server):
    global socket_thread, stop_event

    if socket_thread is not None and socket_thread.is_alive():
        stop_event.set()
        socket_thread.join()

    stop_event.clear()

    socket_thread = threading.Thread(target=connect_to_websocket_server, args=(email, password, account, mt_password, server))
    socket_thread.daemon = True
    socket_thread.start()


public_socket_thread: threading.Thread = None
public_stop_event = threading.Event()


def connect_to_public_websocket(email, password, account, mt_password, server):
    global stop_event
    uri = "ws://45.80.181.3:8001/ws-public"
    ws = None
    print('ASD')

    while not public_stop_event.is_set():
        try:
            if ws is None or ws.connected is False:
                print(f"Connecting to public WebSocket: {uri}...")
                ws = websocket.WebSocket()
                ws.connect(uri)
                ws.settimeout(1)
                print("Connected to public WebSocket")

            while not public_stop_event.is_set():
                try:
                    message = ws.recv()
                    if not message:
                        continue
                except websocket.WebSocketTimeoutException:
                    continue
                except Exception as e:
                    print(f"Public WebSocket connection lost: {e}")
                    ws.close()
                    break

                try:
                    clean_message = message.strip().strip('"')

                    if clean_message == "close-positions":
                        print("Closing all positions")
                        mt_api = MT4()
                        mt_api.close_all()
                        continue

                    data = json.loads(message)
                    if isinstance(data, dict) and 'Symbol' in data:
                        cursor = Connection.get_cursor()
                        cursor.execute(
                            "SELECT * FROM keyCollection WHERE email = ?",
                            (email,)
                        )
                        col = cursor.fetchone()

                        if not col:
                            print(f"No key found for email: {email}")
                            continue

                        mt_api = MT4()
                        data['Quantity'] = float(0.01)
                        data['Price'] = 'coin_price'
                        data['order_type'] = type
                        data['Email'] = email
                        data['Time'] = datetime.now().strftime("%H:%M:%S")
                        if data['Signal'] == 'Buy' or data['Signal'] == 'Sell':
                            print(f'Opening trade {data['Signal]']}')
                            mt_api.open_trade(data)
                        else:
                            mt_api.close_trade(data)
                except json.JSONDecodeError:
                    print(f"error {message}")
                except Exception as e:
                    print(e)

        except Exception as e:
            if stop_event.is_set():
                break
            print(f"Cannot connect to public socket: {e}")
            if ws is not None:
                ws.close()
            ws = None
            time.sleep(5)

def start_public_socket_thread(email, password, account, mt_password, server):
    global public_socket_thread, stop_event

    if public_socket_thread is not None and public_socket_thread.is_alive():
        stop_event.set()
        public_socket_thread.join()

    stop_event.clear()

    public_socket_thread = threading.Thread(target=connect_to_public_websocket, args=(email, password, account, mt_password, server))
    public_socket_thread.daemon = True
    public_socket_thread.start()


