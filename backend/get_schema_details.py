from database import get_db_connection
import json

def get_schema():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [list(t.values())[0] for t in cursor.fetchall()]
    
    schema = {}
    for table in tables:
        cursor.execute(f"DESCRIBE {table}")
        columns = cursor.fetchall()
        schema[table] = columns
        
    conn.close()
    return schema

if __name__ == "__main__":
    schema = get_schema()
    with open("db_schema_details.json", "w") as f:
        json.dump(schema, f, indent=4)
    print("Schema details saved to db_schema_details.json")
