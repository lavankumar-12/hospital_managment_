import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key_change_in_prod'
    DB_HOST = os.environ.get('DB_HOST') or '127.0.0.1'
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or '9885'
    DB_NAME = os.environ.get('DB_NAME') or 'hospital_db'
    SMS_API_KEY = os.environ.get('SMS_API_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
