import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from tradingbinance.Binaceapi import BinanceApi

def get_spot_price(symbol):
    try:
        Api = BinanceApi()
        price = Api.get_spot_price(symbol)
        return price
    except Exception as e:
        print('Got An Exception By give_me_symbol_price()',e)

def futures_exchange_info(symbol):
    try:
        Api = BinanceApi()
        price = Api.futures_exchange_info(symbol)
        return price
    except Exception as e:
        print('Got An Exception By give_me_symbol_price()',e)


def get_future_price(symbol):
    try:
        Api = BinanceApi()
        price = Api.get_future_price(symbol)
        return price
    except Exception as e:
        print('Got An Exception By get_future_price()',e)
