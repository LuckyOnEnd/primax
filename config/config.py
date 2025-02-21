import os
from dotenv import load_dotenv
load_dotenv()

class Config:

    Captcha_API = os.getenv('twocaptchaKey')
    Username = os.getenv('username')
    password = os.getenv('password')
    api_key = os.getenv('Binacekey')  
    api_sec = os.getenv('binacesecret')  
    db_user = os.getenv("DB_USER", "admin")
    db_password = os.getenv("DB_PASSWORD", "admin")
    db_Host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "27017")
    db_name = os.getenv("DB_NAME", "mydatabase")

    mongoUri ="mongodb+srv://lckyoneend:Admin123@devmainops.oefglpo.mongodb.net/?retryWrites=true&w=majority&appName=Devmainops"

    COOKIES_PATH = 'local/cookies.json'

