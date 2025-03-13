import sqlite3
from werkzeug.security import generate_password_hash
import os
from config.config import Config


import os
import sys

def get_db_path():
    if getattr(sys, "frozen", False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    db_path = os.path.join(current_dir, "database", "tradeview.db")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    return db_path



class Connection:
    _conn = None
    _cursor = None

    @classmethod
    def get_connection(cls):
        if cls._conn is None:
            try:
                db_path = get_db_path()
                cls._conn = sqlite3.connect(db_path, check_same_thread=False)
                cls._cursor = cls._conn.cursor()
                print("Successfully connected to SQLite database!")
                cls._create_tables()
            except Exception as e:
                print(f"Error connecting to SQLite: {e}")
                cls._conn = None
                cls._cursor = None
        return cls._conn

    @classmethod
    def get_cursor(cls):
        if cls._cursor is None:
            cls.get_connection()
        return cls._cursor

    @classmethod
    def _create_tables(cls):
        cursor = cls.get_cursor()
        if cursor:
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    password TEXT NOT NULL
                )
            '''
                )

            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS keyCollection (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key TEXT,
                    api_sec TEXT,
                    type TEXT,
                    email TEXT NOT NULL,
                    amount REAL,
                    trading_view_login TEXT,
                    trading_view_password TEXT,
                    trading_view_chart_link TEXT,
                    subscription_type TEXT,
                    FOREIGN KEY (email) REFERENCES users (email)
                )
            '''
                )

            cursor.execute(
                '''
                            CREATE TABLE IF NOT EXISTS logs (
                                type TEXT,
                                Price REAL,
                                Symbol TEXT,
                                Time TEXT,
                                Signal TEXT,
                                Quantity REAL,
                                PositionOpened DATETIME,
                                commission REAL,
                                realized_pnl REAL
                            )
                        '''
                )
            cls._conn.commit()
            print("Database tables created or verified.")

    @classmethod
    def create_default_user(cls):
        conn = cls.get_connection()
        cursor = cls.get_cursor()
        if conn and cursor:
            cursor.execute("SELECT * FROM users WHERE email = ?", ("default@example.com",))
            existing_user = cursor.fetchone()

            if existing_user is None:
                password_hash = generate_password_hash("123321")
                cursor.execute(
                    """
                    INSERT INTO users (email, password)
                    VALUES (?, ?)
                """, ("default@example.com", password_hash)
                    )

                cursor.execute(
                    """
                    INSERT INTO keyCollection (
                        api_key, api_sec, type, email, amount,
                        trading_view_login, trading_view_password, 
                        trading_view_chart_link, subscription_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                        Config.api_key,
                        Config.api_sec,
                        'future',
                        "default@example.com",
                        20,
                        None,
                        None,
                        None,
                        'essential'
                    )
                    )

                conn.commit()
                print("Default user created successfully.")
            else:
                print("Default user already exists.")

    @classmethod
    def close(cls):
        if cls._conn:
            cls._conn.close()
            cls._conn = None
            cls._cursor = None


conn = Connection.get_connection()
Connection.create_default_user()


def get_key_col():
    cursor = Connection.get_cursor()
    cursor.execute("SELECT * FROM keyCollection")
    return cursor.fetchall()


def get_users_col():
    cursor = Connection.get_cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


def get_logs_col():
    cursor = Connection.get_cursor()
    cursor.execute("SELECT * FROM logs")
    return cursor.fetchall()


key_col = get_key_col()
user_col = get_users_col()
logs_col = get_logs_col()