from datetime import datetime, timedelta
from time import sleep

import MetaTrader5 as mt5

class MT5:
    def __init__(self, account, password, server):
        if not mt5.initialize():
            exit()

        if not mt5.login(account, password, server):
            mt5.shutdown()
            exit()

    def open_trade(self, data):
        symbol = data['symbol']
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"Error: Symbol {symbol} unavailable f{datetime.utcnow()}")
            return None

        if not symbol_info.visible or symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_DISABLED:
            print(f"Error: Trade for {symbol} unavailable f{datetime.utcnow()}")
            return None

        price = mt5.symbol_info_tick(symbol).ask
        if price == 0:
            print(f"Error: Cannot receive price for {symbol}")
            return None

        amount = data['amount']
        lot = amount / price
        lot_step = symbol_info.volume_step
        lot = max(symbol_info.volume_min, round(lot / lot_step) * lot_step)
        lot = round(lot, 8)

        order_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": 0.01,
            "type": mt5.ORDER_TYPE_BUY,
            "price": price,
            "deviation": 1,
            "magic": 0,
            "comment": f"Buy {symbol} for {amount} USDT",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(order_request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Error while opening: {result.retcode}")
            return None
        else:
            # orders = mt5.orders_get(ticket=result.order)
            # if orders:
            #     deal = orders[0]
            try:
                self._append_commission_and_realized_pnl(data, result.order)
            except Exception as e:
                print(f"Cannot get commission and profit: {e}")
            return result.order

    def close_trade(self, data):
        positions = mt5.positions_get()

        if positions is None or len(positions) == 0:
            print(f"Positions not found {datetime.utcnow()}")
            return

        symbol = data['symbol']
        for pos in positions:
            if pos.symbol == symbol:
                print(
                    f"Position found: {pos.ticket} | Symbol: {pos.symbol} | Lot: {pos.volume}"
                )

                close_request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                    "position": pos.ticket,
                    "deviation": 20,
                    "magic": 0,
                    "comment": "Close order",
                }

                result = mt5.order_send(close_request)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"Error while close order {pos.ticket}: {result.comment}")
                else:
                    print(f"Order {pos.ticket} успешно закрыт!")

    def _append_commission_and_realized_pnl(self, data_dict, order_id):
        try:
            sleep(1)
            now = datetime.now()
            date_to = now + timedelta(days=2)
            history_deal = mt5.history_deals_get(now, date_to)
            for deal in history_deal:
                if deal.order == order_id:
                    commission = deal.commission
                    profit = deal.prift
                    data_dict.update(
                        {"commission": commission, "realized_pnl": profit}
                    )
                    break
        except Exception as e:
            print('Facing Issue While adding commission and profit', e)