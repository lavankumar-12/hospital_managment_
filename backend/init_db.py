import pymysql
import bcrypt
import logging
import os
from config import Config

def seed_pharmacist(cursor):
    cursor.execute("SELECT * FROM users WHERE email = 'pharmacist@hospital.com'")
    if not cursor.fetchone():
        pw_hash = bcrypt.hashpw('pharmacy123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'pharmacist')", 
                       ('pharmacist@hospital.com', pw_hash))
        print("Pharmacist user seeded: pharmacist@hospital.com / pharmacy123")


def get_db_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Read schema
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(basedir, 'database', 'schema.sql')
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    # Execute schema commands
    # Use simple splitting for this
    commands = schema.split(';')
    
    for command in commands:
        if command.strip():
            try:
                cursor.execute(command)
            except pymysql.Error as err:
                print(f"Error executing command: {err}")
    
    print("Database initialized.")
    
    # Reconnect to the specific database to seed data
    conn.close()
    conn = pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()
    
    # Check if admin exists
    cursor.execute("SELECT * FROM users WHERE email = 'admin@hospital.com'")
    if not cursor.fetchone():
        # Create Admin
        pw_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'admin')", ('admin@hospital.com', pw_hash))
        
    # Create Departments (Run always to ensure new ones are added)
    depts = ['Cardiology', 'Neurology', 'Orthopedics', 'Pediatrics', 'General Medicine','Dermatology','Dental','Gynaecology']
    for d in depts:
        # Check if exists
        cursor.execute("SELECT id FROM departments WHERE name = %s", (d,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO departments (name, description) VALUES (%s, %s)", (d, f"{d} Department"))
            
        
    # Check if doctor exists
    cursor.execute("SELECT * FROM users WHERE email = 'doctor@hospital.com'")
    if not cursor.fetchone():
        # Create Doctor User
        pw_hash = bcrypt.hashpw('doctor123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'doctor')", ('doctor@hospital.com', pw_hash))
        doc_user_id = cursor.lastrowid
        
        # Get Dept ID
        cursor.execute("SELECT id FROM departments WHERE name = 'Cardiology'")
        dept_id = cursor.fetchone()['id']
        
        # Create Doctor Profile
        cursor.execute("INSERT INTO doctors (user_id, department_id, full_name, specialization, experience) VALUES (%s, %s, 'Stephen Strange', 'Surgeon', 15)", 
                       (doc_user_id, dept_id))
        print("Doctor seed data injected.")

    # Seed Medicines
    cursor.execute("SELECT COUNT(*) as count FROM medicines")
    if cursor.fetchone()['count'] == 0:
        # Get Dept IDs
        cursor.execute("SELECT id FROM departments WHERE name = 'Cardiology'")
        cardio_id = cursor.fetchone()['id']
        
        cursor.execute("SELECT id FROM departments WHERE name = 'General Medicine'")
        gen_med_id = cursor.fetchone()['id'] if cursor.rowcount > 0 else cardio_id # Fallback

        meds = [
            (cardio_id, 'Atorvastatin', 'Cholesterol medication', 15.50, 100),
            (cardio_id, 'Aspirin', 'Blood thinner', 5.00, 500),
            (gen_med_id, 'Paracetamol', 'Pain reliever', 2.50, 1000),
            (gen_med_id, 'Amoxicillin', 'Antibiotic', 12.00, 200),
            (gen_med_id, 'Vitamin C', 'Supplement', 8.00, 300)
        ]
        
        for m in meds:
            cursor.execute("INSERT INTO medicines (department_id, name, description, price, stock_quantity) VALUES (%s, %s, %s, %s, %s)", m)
        print("Medicines seeded.")

    seed_pharmacist(cursor)


if __name__ == '__main__':
    init_db()
