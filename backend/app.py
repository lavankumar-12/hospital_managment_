from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
from routes.auth import auth_bp
from routes.patient import patient_bp
from routes.doctor import doctor_bp
from routes.admin import admin_bp
from routes.pharmacy import pharmacy_bp
from config import Config

from flask.json.provider import DefaultJSONProvider
import datetime
from decimal import Decimal

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, datetime.time):
            return obj.isoformat()
        if isinstance(obj, datetime.timedelta):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.json = CustomJSONProvider(app)
app.config.from_object(Config)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(patient_bp, url_prefix='/api/patient')
app.register_blueprint(doctor_bp, url_prefix='/api/doctor')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(pharmacy_bp, url_prefix='/api/pharmacy')

@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
