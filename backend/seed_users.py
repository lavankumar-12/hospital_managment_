from database import get_db_connection
import bcrypt

def seed_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Create Admin
        admin_email = 'admin@hospital.com'
        admin_pass = 'lavan'
        
        cursor.execute("SELECT id FROM users WHERE email = %s", (admin_email,))
        if not cursor.fetchone():
            hashed = bcrypt.hashpw(admin_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            # Assuming role is 'admin'
            cursor.execute("INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'admin') RETURNING id", (admin_email, hashed))
            uid = cursor.fetchone()['id']
            print(f"Admin created: {admin_email} (ID: {uid})")
        else:
            print(f"Admin already exists: {admin_email}")

        # 2. Create Pharmacist
        pharm_email = 'pharmacist@hospital.com'
        pharm_pass = 'pharmacy123'
        
        cursor.execute("SELECT id FROM users WHERE email = %s", (pharm_email,))
        if not cursor.fetchone():
            hashed = bcrypt.hashpw(pharm_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'pharmacist') RETURNING id", (pharm_email, hashed))
            uid = cursor.fetchone()['id']
            print(f"Pharmacist created: {pharm_email} (ID: {uid})")
        else:
            print(f"Pharmacist already exists: {pharm_email}")
            
        conn.commit()
            
    except Exception as e:
        print(f"Error reseeding users: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    seed_users()
