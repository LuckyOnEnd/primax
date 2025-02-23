import sys
import os
from datetime import datetime
from time import sleep

# add main directoty of the project
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
# import config file
from config.config import Config
from helper.Log import insertlog
from binance.client import Client

class OrderData:
    def __init__(self, commission, realized_pnl):
        self.commission = commission
        self.realized_pnl = realized_pnl

class BinanceApi:
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret)

    def get_spot_price(self, symbol):
        btc_price = self.client.get_symbol_ticker(symbol=symbol)
        return btc_price

    def get_future_price(self, symbol):
        market_price = self.client.futures_symbol_ticker(symbol=symbol)['price']
        return market_price

    def futures_exchange_info(self, symbol):
        res = self.client.futures_exchange_info()
        return res

    def check_balance(self):
        account_info = self.client.get_account()
        balances = account_info['balances']
        all_assets = []
        for balance in balances:
            asset = balance['asset']
            free = balance['free']
            all_assets.append({asset: free})
        return all_assets

    def create_order_spot(self, data_dict):
        try:
            signal = data_dict.get('Signal').lower()
            price = data_dict.get('Price')
            quantity = data_dict.get('Quantity')
            symbol = data_dict.get('Symbol')

            symbol_info = self.client.get_symbol_info(symbol)
            lot_size_filter = None

            for filter in symbol_info['filters']:
                if filter['filterType'] == 'LOT_SIZE':
                    lot_size_filter = filter
                    break

            if lot_size_filter:
                step_size = float(lot_size_filter['stepSize'])
                min_qty = float(lot_size_filter['minQty'])

                quantity = round(quantity / step_size) * step_size

                if quantity < min_qty:
                    print(f"Error: Quantity must be greater than or equal to {min_qty}")
                    return None

            if 'buy' not in signal:
                balance_info = self.client.get_asset_balance(
                    symbol[:-4]
                    )
                available_balance = float(balance_info['free'])

                if 'bsl' in signal or 'btp' in signal and available_balance < quantity:
                    quantity = available_balance

            if 'buy' in signal:
                try:
                    order = self.client.create_order(
                        symbol=symbol,
                        side=Client.SIDE_BUY,
                        type=Client.ORDER_TYPE_MARKET,
                        quantity=quantity
                    )
                    print('Order Created Successfully......')
                    insertlog(data_dict)
                    return order

                except Exception as e:
                    print('Error while creating buy spot order', e)

            elif 'btp' in signal or 'bsl' in signal:
                try:
                    order = self.client.create_order(
                        symbol=symbol,
                        side=Client.SIDE_SELL,
                        type=Client.ORDER_TYPE_MARKET,
                        quantity=quantity
                    )
                    print(f"Market sell order created for {signal.upper()}")
                    insertlog(data_dict)
                    return order

                except Exception as e:
                    print(f'Error while creating {signal.upper()} spot order', e)

        except Exception as e:
            print('Facing Issue While Create Order For Spot', e)

    def create_order_future(self, data_dict):
        try:
            signal = data_dict.get('Signal').lower()
            quantity = data_dict.get('Quantity')
            symbol = data_dict.get('Symbol')

            position = self.client.futures_position_information(symbol=symbol)

            if 'buy' in signal:
                try:
                    if len(position) > 0:
                        self._close_buy_order(symbol, position[0]['positionAmt'])

                    order = self.client.futures_create_order(
                        symbol=symbol, side=Client.SIDE_BUY, type=Client.FUTURE_ORDER_TYPE_MARKET,
                        quantity=quantity
                        )
                    print('Futures Order Successful: for buy')
                    self._append_commission_and_realized_pnl(data_dict, symbol, order['orderId'])
                    insertlog(data_dict)
                    return order
                except Exception as e:
                    print(f'{datetime.utcnow()} Exception in future create order', e)

            elif 'sell' in signal:
                try:
                    if len(position) > 0:
                        self._close_sell_order(symbol, position[0]['positionAmt'])

                    order = self.client.futures_create_order(
                        symbol=symbol, side=Client.SIDE_SELL, type=Client.FUTURE_ORDER_TYPE_MARKET,
                        quantity=quantity
                        )
                    print('Futures Order Successful: for sell')
                    self._append_commission_and_realized_pnl(data_dict, symbol, order['orderId'])
                    insertlog(data_dict)
                    return order
                except Exception as e:
                    print(f'{datetime.utcnow()} Exception in future create order sell ', e)

            if len(position) < 1:
                print(f'Open positions not found {datetime.utcnow()}')
                return

            if 'btp' in signal:
                try:
                    order = self._close_buy_order(symbol, position[0]['positionAmt'])
                    print('BTP Order Created:')
                    self._append_commission_and_realized_pnl(data_dict, symbol, order['orderId'])
                    insertlog(data_dict)
                    return order
                except Exception as e:
                    print(f'{datetime.utcnow()} Exception in future btp trade', e)

            if 'bsl' in signal:
                try:
                    order = self._close_buy_order(symbol, position[0]['positionAmt'])
                    print('BSL Stop-Loss Order Created:')
                    self._append_commission_and_realized_pnl(data_dict, symbol, order['orderId'])
                    insertlog(data_dict)
                    return order
                except Exception as e:
                    print(f'{datetime.utcnow()} Error in creating BSL stop-loss order', e)

            if 'stp' in signal:
                try:
                    order = self._close_sell_order(symbol, position[0]['positionAmt'])
                    print('STP Order Created:')
                    self._append_commission_and_realized_pnl(data_dict, symbol, order['orderId'])
                    insertlog(data_dict)
                    return order
                except Exception as e:
                    print(f'{datetime.utcnow()} Exception in future stp trade', e)

            if 'ssl' in signal:
                try:
                    order = self._close_sell_order(symbol, position[0]['positionAmt'])
                    print('STP Order Created:')
                    self._append_commission_and_realized_pnl(data_dict, symbol, order['orderId'])
                    insertlog(data_dict)
                    return order
                except Exception as e:
                    print(f'{datetime.utcnow()} Exception in future ssl trade', e)

        except Exception as e:
            print('Facing Issue While Create Order For Future', e)

    def _close_buy_order(self, symbol, positionAmt):
        order = self.client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.FUTURE_ORDER_TYPE_MARKET,
            quantity=abs(float(positionAmt)),
        )

        return order

    def _close_sell_order(self, symbol, positionAmt):
        order = self.client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_BUY,
            type=Client.FUTURE_ORDER_TYPE_MARKET,
            quantity=abs(float(positionAmt)),
        )

        return order

    def _append_commission_and_realized_pnl(self, data_dict, symbol, order_id):
        try:
            sleep(1)
            order_data = self._get_order_data(order_id, symbol)
            data_dict.update({"commission": order_data.commission, "realized_pnl": order_data.realized_pnl})
        except Exception as e:
            print('Facing Issue While Create Order For Future', e)

    def _get_order_data(self, order_id, symbol) -> OrderData:
        try:
            trades = self.client.futures_account_trades(symbol=symbol)
            trade_info = next((t for t in trades if t['orderId'] == order_id), None)

            if trade_info:
                commission = float(trade_info['commission'])
                realized_pnl = float(trade_info['realizedPnl'])
                return OrderData(commission, realized_pnl)
        except Exception as e:
            print('Facing Issue While Create Order For Future', e)
