
import pymysql
from database import get_db_connection

def migrate():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if column exists
        cursor.execute("SHOW COLUMNS FROM orders LIKE 'payment_method'")
        result = cursor.fetchone()
        
        if not result:
            print("Adding payment_method column to orders table...")
            cursor.execute("ALTER TABLE orders ADD COLUMN payment_method ENUM('cash', 'online') NOT NULL DEFAULT 'cash'")
            print("Migration successful.")
        else:
            print("Column payment_method already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
