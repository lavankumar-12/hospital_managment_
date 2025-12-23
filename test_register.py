
import requests
import json

url = "http://127.0.0.1:5001/api/auth/register"
data = {
    "email": "test_patient_v2@example.com",
    "password": "password123",
    "full_name": "Test Patient V2",
    "age": 30,
    "gender": "Male",
    "phone": "1234567890"
}

try:
    print(f"Sending POST to {url}")
    res = requests.post(url, json=data)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
except Exception as e:
    print(f"Connection Failed: {e}")
