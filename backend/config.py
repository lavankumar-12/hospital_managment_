import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key_change_in_prod'
    DB_HOST = '127.0.0.1'
    DB_USER = 'root'
    DB_PASSWORD = '9885'
    DB_NAME = 'hospital_db'
    SMS_API_KEY = os.environ.get('SMS_API_KEY')
