import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key_change_in_prod'
    # Neon DB Config
    DB_HOST = os.environ.get('DB_HOST') or 'ep-damp-lake-a1v7c9hw-pooler.ap-southeast-1.aws.neon.tech'
    DB_USER = os.environ.get('DB_USER') or 'neondb_owner'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'npg_iCZtHBF1bET4'
    DB_NAME = os.environ.get('DB_NAME') or 'neondb'
    # SSL Mode is required for Neon
    DB_SSL_MODE = 'require'
    SMS_API_KEY = os.environ.get('SMS_API_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Twilio Config
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
