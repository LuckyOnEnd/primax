from pymongo import MongoClient
import certifi
from werkzeug.security import generate_password_hash
import time
from config.config import Config
import os
import subprocess

def start_mongodb():
    try:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"Current dir: {current_dir}")

        mongodb_path = os.path.join(current_dir, "mongodb", "bin", "mongod.exe")
        print(f"Mongo Path: {mongodb_path}")
        db_path = os.path.join(current_dir, "mongodb", "data")

        if not os.path.exists(db_path):
            print('Creating database directory...')
            os.makedirs(db_path)

        print('Starting MongoDB...')
        process = subprocess.Popen([mongodb_path, "--dbpath", db_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        return process
    except Exception as e:
        print(e)
        return None


class Connection:
    _client = None
    _db = None
    _key_col = None
    _logs_col = None
    _users_col = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            try:
                start_mongodb()
                print("Attempting to connect to MongoDB...")
                ca = certifi.where()
                cls._client = MongoClient(Config.mongoUri)
                #cls._client=MongoClient(Config.db_Host,int(Config.db_port))
                cls._client.admin.command('ping') 
                print("Successfully connected to MongoDB!")
            except Exception as e:
                print(f"Error connecting to MongoDB: {e}")
                cls._client = None
        return cls._client

    @classmethod
    def get_db(cls):
        if cls._db is None:
            client = cls.get_client()
            if client:
                cls._db = client['tradeView'] 
                print("Connected to database 'tradeView'.")
            else:
                print("MongoDB client is not connected.")
        return cls._db

    @classmethod
    def get_key_col(cls):
        if cls._key_col is None:
            db = cls.get_db()
            if db is not None:
                cls._key_col = db['keyCollection']
                print("Accessed collection 'keyCollection'.")
            else:
                print("Database 'tradeView' is not accessible.")
        return cls._key_col

    @classmethod
    def get_logs_col(cls):
        if cls._logs_col is None:
            db = cls.get_db()
            if db is not None:
                cls._logs_col = db['logs']
            else:
                print("Database 'tradeView' is not accessible.")
        return cls._logs_col

    @classmethod
    def get_users_col(cls):
        if cls._users_col is None:
            db = cls.get_db()
            if db is not None:
                cls._users_col = db['users']
            else:
                print("Database 'users' is not accessible.")
        return cls._users_col

    @classmethod
    def create_default_user(cls):
        users_col = cls.get_db()['users']
        existing_user = users_col.find_one({})
        if existing_user is None:
            password_hash = generate_password_hash("123321")
            user_data = {
                'password': password_hash,
                'user_id': 1
            }
            users_col.insert_one(user_data)
            key_col = cls.get_key_col()
            key_col.insert_one({
                'api_key': Config.api_key,
                'api_sec': Config.api_sec,
                'type': 'future',
                'user_id': 1,
                'amount': 20,
                'trading_view_login': None,
                'trading_view_password': None,
                'trading_view_chart_link': None
            })

            print(f"User with user_id '{1}' created successfully.")
        else:
            print(f"Admin already exists.")

key_col = Connection.get_key_col()
user_col = Connection.get_users_col()
logs_col = Connection.get_logs_col()
Connection.create_default_user()
