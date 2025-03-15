import shutil
import sqlite3
from werkzeug.security import generate_password_hash
import os
from config.config import Config


import os
import sys

def get_db_path():
    if sys.platform == "win32":
        target_base_dir = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Primex")
    else:
        target_base_dir = os.path.join("/usr/local", "primex")

    target_db_dir = os.path.join(target_base_dir, "database")
    target_db_path = os.path.join(target_db_dir, "tradeview.db")

    if getattr(sys, "frozen", False):  # Nuitka
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    source_db_path = os.path.join(current_dir, "database", "tradeview.db")

    if os.path.exists(source_db_path) and not os.path.exists(target_db_path):
        try:
            os.makedirs(target_db_dir, exist_ok=True)
            shutil.copy2(source_db_path, target_db_path)
            print(f"Copied database from {source_db_path} to {target_db_path}")
        except PermissionError:
            print(f"Permission denied to copy database to {target_db_path}. Using source path.")
            return source_db_path
        except Exception as e:
            print(f"Error copying database: {e}")
            return source_db_path

    if not os.path.exists(target_db_dir):
        try:
            os.makedirs(target_db_dir, exist_ok=True)
        except PermissionError:
            print(f"Permission denied to create {target_db_dir}. Using source path.")
            return source_db_path

    print(f"Database path: {target_db_path}")
    return target_db_path

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
                    order_type TEXT,
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
                                order_type TEXT,
                                Price REAL,
                                Symbol TEXT,
                                Time TEXT,
                                Signal TEXT,
                                Quantity REAL,
                                PositionOpened DATETIME,
                                commission REAL,
                                realized_pnl REAL,
                                Email TEXT
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
                        api_key, api_sec, order_type, email, amount,
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