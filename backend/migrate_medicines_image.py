
import pymysql
from database import get_db_connection

def migrate_image_url():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW COLUMNS FROM medicines LIKE 'image_url'")
        if not cursor.fetchone():
            print("Adding image_url to medicines table...")
            cursor.execute("ALTER TABLE medicines ADD COLUMN image_url VARCHAR(500) DEFAULT NULL")
            print("Done.")
        else:
            print("column image_url already exists")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_image_url()
