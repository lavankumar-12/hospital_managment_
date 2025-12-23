
import pymysql
import bcrypt
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.database import get_db_connection

def create_pharmacist():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    email = "pharma@test.com"
    password = "password"
    role = "pharmacist"
    
    try:
        # Check if exists
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            print("Pharmacist user already exists.")
            return

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)", (email, hashed, role))
        conn.commit()
        print("Pharmacist user created successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_pharmacist()
