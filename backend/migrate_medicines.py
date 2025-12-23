import pymysql
from database import get_db_connection

def migrate():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("Checking if image_url column exists...")
        cursor.execute("SHOW COLUMNS FROM medicines LIKE 'image_url'")
        if cursor.fetchone():
            print("Column image_url already exists.")
        else:
            print("Adding image_url column to medicines table...")
            cursor.execute("ALTER TABLE medicines ADD COLUMN image_url VARCHAR(500) DEFAULT NULL")
            print("Column added successfully.")
            
            # Update existing medicines with dummy images
            print("Updating existing medicines with specific images...")
            updates = [
                ('Atorvastatin', 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=400'),
                ('Aspirin', 'https://images.unsplash.com/photo-1628771065518-0d82f1938462?auto=format&fit=crop&q=80&w=400'),
                ('Paracetamol', 'https://images.unsplash.com/photo-1584017911766-d451b3d0e843?auto=format&fit=crop&q=80&w=400'),
                ('Amoxicillin', 'https://images.unsplash.com/photo-1471864190281-a93a3070b6de?auto=format&fit=crop&q=80&w=400'),
                ('Vitamin C', 'https://images.unsplash.com/photo-1512069772995-ec65ed45afd6?auto=format&fit=crop&q=80&w=400')
            ]
            
            for name, url in updates:
                cursor.execute("UPDATE medicines SET image_url = %s WHERE name = %s", (url, name))
            
            # Set a default for any others
            cursor.execute("UPDATE medicines SET image_url = 'https://images.unsplash.com/photo-1585435557343-3b092031a831?auto=format&fit=crop&q=80&w=400' WHERE image_url IS NULL")
            print("Existing medicines updated.")

    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
