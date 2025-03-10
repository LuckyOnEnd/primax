import os
from dotenv import load_dotenv
load_dotenv()

class Config:

    Captcha_API = '20889fecf36a0d81df702d81119d8f03'
    Username = os.getenv('username')
    password = os.getenv('password')
    api_key = os.getenv('Binacekey')
    api_sec = os.getenv('binacesecret')
    db_user = os.getenv("DB_USER", "admin")
    db_password = os.getenv("DB_PASSWORD", "admin")
    db_Host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "27017")
    db_name = os.getenv("DB_NAME", "mydatabase")
    trading_view_login = os.getenv("TRADING_VIEW_ID")
    trading_view_password = os.getenv("TRADING_VIEW_PASSWORD")
    chart_link = os.getenv("CHART_LINK")

    mongoUri = os.getenv("MONGODB_URI")

    COOKIES_PATH = 'local/cookies.json'

