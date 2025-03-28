import re
from datetime import datetime, timedelta
from time import sleep
import zmq

class MT4:
    def __init__(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")

    def open_trade(self, data):
        symbol = data['Symbol']
        symbol = symbol.split(',')[0].strip()
        if 'USDT' in symbol:
            symbol = re.sub(r'USDT.*', 'USD.a', symbol)

        if not symbol.endswith('.e'):
            symbol += '.e'

        amount = data['Quantity']
        self.socket.send_string(f"{"SELL" if data["Signal"] == "Sell" else "BUY"} {symbol} {0.01}")

    def close_trade(self, data):
        symbol = data['Symbol']
        symbol = symbol.split(',')[0].strip()
        if 'USDT' in symbol:
            symbol = re.sub(r'USDT.*', 'USD.a', symbol)

        if not symbol.endswith('.e'):
            symbol += '.e'

        self.socket.send_string(f"{"CLOSE"} {symbol}")

    def _append_commission_and_realized_pnl(self, data_dict, order_id):
        try:
            sleep(1)
            now = datetime.now()
            date_to = now + timedelta(days=2)
            history_deal = mt5.history_deals_get(now, date_to)
            for deal in history_deal:
                if deal.order == order_id:
                    commission = deal.commission
                    profit = deal.profit
                    data_dict.update(
                        {"commission": commission, "realized_pnl": profit}
                    )
                    break
        except Exception as e:
            print('Facing Issue While adding commission and profit', e)