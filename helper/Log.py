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

        query = "INSERT INTO logs (message) VALUES (?)"
        cursor.execute(query, (data.get('message'),))
        conn.commit()

        class InsertResult:
            def __init__(self, id):
                self.inserted_id = id

        last_id = cursor.lastrowid
        return InsertResult(last_id)

    except Exception as e:
        print('got exception as ', e)
        return None

