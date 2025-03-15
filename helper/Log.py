import sys
import os
# add main directoty of the project
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR)) 
from database.connection import Connection


def insertlog(data):
    try:
        cursor = Connection.get_cursor()
        conn = Connection.get_connection()

        query = """
            INSERT INTO logs (
                order_type, Price, Symbol, Time, Signal, Quantity, 
                PositionOpened, commission, realized_pnl, Email
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            data.get('order_type'),
            data.get('Price'),
            data.get('Symbol'),
            data.get('Time'),
            data.get('Signal'),
            data.get('Quantity'),
            data.get('PositionOpened'),
            data.get('commission'),
            data.get('realized_pnl'),
            data.get('Email')
        )

        cursor.execute(query, values)
        conn.commit()

        class InsertResult:
            pass

        return InsertResult()

    except Exception as e:
        print('got exception as ', e)
        return None

