from tradingbinance.Binaceapi  import BinanceApi

# make function for all
def main_api_container(data):
    binance_api = BinanceApi()

    if data.get('type') == 'spot':
        binance_api.create_order_spot(data)
    else:
        binance_api.create_order_future(data)
        