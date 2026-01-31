from database import get_db_connection
import json

def dump_schema():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [list(t.values())[0] for t in cursor.fetchall()]
    
    full_schema = {}
    for table in tables:
        cursor.execute(f"DESCRIBE {table}")
        full_schema[table] = cursor.fetchall()
        
    with open("full_db_schema.json", "w") as f:
        json.dump(full_schema, f, indent=4)
    conn.close()

if __name__ == "__main__":
    dump_schema()
