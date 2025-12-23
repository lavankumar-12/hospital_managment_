import pymysql
import bcrypt
from config import Config

def test_login_logic(test_email, test_password):
    print(f"--- Testing Login for: {test_email} / {test_password} ---")
    
    conn = pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )
    
    try:
        with conn.cursor() as cursor:
            # 1. Fetch User
            print("1. Querying database...")
            cursor.execute("SELECT id, password_hash, role FROM users WHERE email = %s", (test_email,))
            user = cursor.fetchone()
            
            if not user:
                print("❌ User NOT FOUND in database.")
                return

            print(f"✅ User found: ID={user.get('id')}, Role={user.get('role')}")
            
            stored_hash = user['password_hash']
            print(f"   Stored Hash: {stored_hash} (Type: {type(stored_hash)})")
            
            # 2. Check Password
            print("2. Verifying password...")
            
            # Simulate exactly what the route does
            try:
                # Ensure password is bytes
                input_bytes = test_password.encode('utf-8')
                
                # Handle stored hash
                if isinstance(stored_hash, str):
                    hash_bytes = stored_hash.encode('utf-8')
                elif isinstance(stored_hash, bytes):
                    hash_bytes = stored_hash
                else:
                    print(f"❌ Unknown hash type: {type(stored_hash)}")
                    return

                print(f"   Input Bytes: {input_bytes}")
                print(f"   Hash Bytes:  {hash_bytes[:20]}...")

                if bcrypt.checkpw(input_bytes, hash_bytes):
                    print("✅ Password MATCHES!")
                else:
                    print("❌ Password DOES NOT MATCH.")
                    
            except Exception as e:
                print(f"❌ Error during checkpw: {e}")

    finally:
        conn.close()

def display_all_users():
    print("\n--- All Users in DB ---")
    conn = pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, email, role FROM users")
        users = cursor.fetchall()
        for u in users:
            print(u)
    conn.close()

def check_content():
    conn = pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    with conn.cursor() as cursor:
        print("\n--- Database Content Check ---")
        tablenames = ['users', 'doctors', 'patients', 'medicines']
        for t in tablenames:
            cursor.execute(f"SELECT COUNT(*) as c FROM {t}")
            print(f"Table {t}: {cursor.fetchone()['c']} rows")
            
        # List medicines if any
        cursor.execute("SELECT id, name FROM medicines LIMIT 5")
        print("Medicines Sample:", cursor.fetchall())
        
        # List doctors if any
        cursor.execute("SELECT id, full_name FROM doctors LIMIT 5")
        print("Doctors Sample:", cursor.fetchall())

    conn.close()

if __name__ == "__main__":
    check_content()
    # display_all_users()
    # test_login_logic('pharmacist@hospital.com', 'pharmacy123')


def display_all_users():
    print("\n--- All Users in DB ---")
    conn = pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, email, role FROM users")
        users = cursor.fetchall()
        for u in users:
            print(u)
    conn.close()
