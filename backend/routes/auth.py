from flask import Blueprint, request, jsonify
import bcrypt
import jwt
import datetime
from database import get_db_connection
from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = 'patient' # Only patients self-register
    
    # Patient details
    full_name = data.get('full_name')
    age = data.get('age')
    gender = data.get('gender')
    phone = data.get('phone')

    if not email or not password or not full_name:
        return jsonify({"message": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"message": "User already exists"}), 409
        
        # Create User
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s) RETURNING id", (email, hashed, role))
        user_id = cursor.fetchone()['id']
        
        # Create Patient Profile
        cursor.execute("INSERT INTO patients (user_id, full_name, age, gender, phone) VALUES (%s, %s, %s, %s, %s)", 
                       (user_id, full_name, age, gender, phone))
        
        return jsonify({"message": "Registration successful"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, password_hash, role FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
             print(f"Login failed: User {email} not found")
             return jsonify({"message": "User not found"}), 401

        stored_hash = user['password_hash']
        
        # Ensure correct encoding for bcrypt
        if isinstance(stored_hash, str):
            hash_bytes = stored_hash.encode('utf-8')
        elif isinstance(stored_hash, bytes):
            hash_bytes = stored_hash
        else:
            # Fallback for unexpected types
            hash_bytes = str(stored_hash).encode('utf-8')

        if bcrypt.checkpw(password.encode('utf-8'), hash_bytes):
            token = jwt.encode({
                'user_id': user['id'],
                'role': user['role'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, Config.SECRET_KEY, algorithm="HS256")
            
            return jsonify({
                "token": token,
                "role": user['role'],
                "user_id": user['id']
            }), 200
        else:
            print(f"Login failed: Password mismatch for {email}")
            return jsonify({"message": "Password mismatch"}), 401
    except Exception as e:
        print(f"Login Error: {e}")
        return jsonify({"message": "Internal Server Error"}), 500
    finally:
        cursor.close()
        conn.close()

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    data = request.json
    user_id = data.get('user_id')
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not user_id or not current_password or not new_password:
        return jsonify({"message": "Missing fields"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current hash
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"message": "User not found"}), 404
            
        stored_hash = user['password_hash']
        if isinstance(stored_hash, str):
            hash_bytes = stored_hash.encode('utf-8')
        else:
            hash_bytes = stored_hash

        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), hash_bytes):
            return jsonify({"message": "Current password incorrect"}), 401
            
        # Update to new password
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("UPDATE users SET password_hash=%s WHERE id=%s", (new_hash, user_id))
        conn.commit()
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
         return jsonify({"message": str(e)}), 500
    finally:
         conn.close()

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    # Helper to get user info from token (Implementation can be middleware, but simple here)
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"message": "Missing token"}), 401
    
    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, email, role FROM users WHERE id = %s", (payload['user_id'],))
        user = cursor.fetchone()
        
        if not user:
             return jsonify({"message": "User not found"}), 404
             
        # Fetch profile if patient or doctor
        profile = None
        if user['role'] == 'patient':
            cursor.execute("SELECT * FROM patients WHERE user_id = %s", (user['id'],))
            profile = cursor.fetchone()
        elif user['role'] == 'doctor':
             cursor.execute("SELECT * FROM doctors WHERE user_id = %s", (user['id'],))
             profile = cursor.fetchone()
             
        return jsonify({"user": user, "profile": profile}), 200
        
    except Exception as e:
        return jsonify({"message": "Invalid token"}), 401
    finally:
        if 'conn' in locals():
            conn.close()
