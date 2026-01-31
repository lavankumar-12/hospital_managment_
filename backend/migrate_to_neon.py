import pymysql
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import datetime
import decimal

# Connection details
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '9885',
    'database': 'hospital_db'
}

NEON_URL = "postgresql://neondb_owner:npg_iCZtHBF1bET4@ep-damp-lake-a1v7c9hw-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

def migrate():
    # Connect to MySQL
    try:
        mysql_conn = pymysql.connect(
            **MYSQL_CONFIG,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Connected to MySQL")
    except Exception as e:
        print(f"MySQL Connection Error: {e}")
        return

    # Connect to Neon
    try:
        pg_conn = psycopg2.connect(NEON_URL)
        pg_conn.autocommit = True
        pg_cursor = pg_conn.cursor()
        print("Connected to Neon PostgreSQL")
    except Exception as e:
        print(f"Neon Connection Error: {e}")
        return

    # Define Schema for PostgreSQL
    schema_queries = [
        "DROP TABLE IF EXISTS notifications CASCADE;",
        "DROP TABLE IF EXISTS order_items CASCADE;",
        "DROP TABLE IF EXISTS orders CASCADE;",
        "DROP TABLE IF EXISTS cart_items CASCADE;",
        "DROP TABLE IF EXISTS medicines CASCADE;",
        "DROP TABLE IF EXISTS prescriptions CASCADE;",
        "DROP TABLE IF EXISTS daily_queues CASCADE;",
        "DROP TABLE IF EXISTS appointments CASCADE;",
        "DROP TABLE IF EXISTS doctor_leaves CASCADE;",
        "DROP TABLE IF EXISTS doctors CASCADE;",
        "DROP TABLE IF EXISTS patients CASCADE;",
        "DROP TABLE IF EXISTS departments CASCADE;",
        "DROP TABLE IF EXISTS users CASCADE;",

        """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE departments (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT
        );
        """,
        """
        CREATE TABLE doctors (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            department_id INT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
            full_name VARCHAR(100) NOT NULL,
            specialization VARCHAR(100),
            experience INT DEFAULT 0,
            phone VARCHAR(20),
            schedule_start TIME DEFAULT '09:00:00',
            schedule_end TIME DEFAULT '17:00:00',
            is_paused BOOLEAN DEFAULT FALSE,
            pause_reason TEXT
        );
        """,
        """
        CREATE TABLE patients (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            full_name VARCHAR(100) NOT NULL,
            age INT,
            gender VARCHAR(20),
            phone VARCHAR(20)
        );
        """,
        """
        CREATE TABLE appointments (
            id SERIAL PRIMARY KEY,
            patient_id INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
            doctor_id INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
            appointment_date DATE NOT NULL,
            appointment_time TIME NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            type VARCHAR(20) DEFAULT 'normal',
            token_number INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reschedule_note TEXT
        );
        """,
        """
        CREATE TABLE doctor_leaves (
            id SERIAL PRIMARY KEY,
            doctor_id INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
            leave_date DATE NOT NULL
        );
        """,
        """
        CREATE TABLE daily_queues (
            id SERIAL PRIMARY KEY,
            doctor_id INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
            queue_date DATE NOT NULL,
            current_token INT DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (doctor_id, queue_date)
        );
        """,
        """
        CREATE TABLE prescriptions (
            id SERIAL PRIMARY KEY,
            appointment_id INT NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
            diagnosis TEXT,
            medicines TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE medicines (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            department_id INT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            stock_quantity INT DEFAULT 0,
            unit VARCHAR(20) DEFAULT 'nm',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_url VARCHAR(500)
        );
        """,
        """
        CREATE TABLE cart_items (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            medicine_id INT NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
            quantity INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, medicine_id)
        );
        """,
        """
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            total_amount DECIMAL(10, 2) NOT NULL,
            status VARCHAR(20) DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            payment_method VARCHAR(20) DEFAULT 'cash'
        );
        """,
        """
        CREATE TABLE order_items (
            id SERIAL PRIMARY KEY,
            order_id INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            medicine_id INT NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
            quantity INT NOT NULL,
            price_at_time DECIMAL(10, 2) NOT NULL
        );
        """,
        """
        CREATE TABLE notifications (
            id SERIAL PRIMARY KEY,
            user_id INT,
            patient_id INT,
            message TEXT NOT NULL,
            type VARCHAR(50),
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            appointment_id INT REFERENCES appointments(id) ON DELETE CASCADE
        );
        """
    ]

    print("Creating tables in Neon...")
    for query in schema_queries:
        try:
            pg_cursor.execute(query)
        except Exception as e:
            print(f"Error executing query: {query[:50]}... Error: {e}")

    # Migrate Data
    tables_to_migrate = [
        'users', 'departments', 'doctors', 'patients', 'appointments', 
        'doctor_leaves', 'daily_queues', 'prescriptions', 'medicines', 
        'cart_items', 'orders', 'order_items', 'notifications'
    ]

    mysql_cursor = mysql_conn.cursor()

    for table in tables_to_migrate:
        print(f"Migrating table: {table}")
        mysql_cursor.execute(f"SELECT * FROM {table}")
        rows = mysql_cursor.fetchall()
        if not rows:
            print(f"No data in {table}")
            continue

        columns = list(rows[0].keys())
        
        # Handle decimal and datetime types for psycopg2
        processed_data = []
        for row in rows:
            val_list = []
            for col in columns:
                val = row[col]
                if isinstance(val, decimal.Decimal):
                    val = float(val)
                elif isinstance(val, (datetime.date, datetime.time, datetime.datetime)):
                    val = val.isoformat()
                val_list.append(val)
            processed_data.append(tuple(val_list))

        placeholders = ",".join(["%s"] * len(columns))
        col_names = ",".join(columns)
        
        insert_query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
        
        try:
            pg_cursor.executemany(insert_query, processed_data)
            print(f"Migrated {len(processed_data)} rows for {table}")
        except Exception as e:
            print(f"Error migrating data for {table}: {e}")

    # Reset sequences
    for table in tables_to_migrate:
        try:
            pg_cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table}")
        except Exception as e:
            print(f"Warning: Could not reset sequence for {table}: {e}")

    mysql_conn.close()
    pg_conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
