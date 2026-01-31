import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from config import Config
from contextlib import contextmanager

# Global Connection Pool
# Min 1 connection, max 20 connections
connection_pool = None

def init_pool():
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                dbname=Config.DB_NAME,
                sslmode='require',
                cursor_factory=RealDictCursor
            )
            print("Database connection pool created successfully")
        except Exception as e:
            print(f"Error creating connection pool: {e}")

class ConnectionProxy:
    def __init__(self, conn, pool):
        self.conn = conn
        self.pool = pool
        self.autocommit = True # Match existing behavior

    def cursor(self, *args, **kwargs):
        return self.conn.cursor(*args, **kwargs)

    def commit(self):
        return self.conn.commit()

    def rollback(self):
        return self.conn.rollback()

    def close(self):
        # Return to pool instead of closing
        if self.pool and self.conn:
            self.pool.putconn(self.conn)
            self.conn = None

    def __getattr__(self, name):
        return getattr(self.conn, name)

def get_db_connection():
    global connection_pool
    if connection_pool is None:
        init_pool()
    
    conn = connection_pool.getconn()
    conn.autocommit = True
    return ConnectionProxy(conn, connection_pool)

# Initialize pool on module load/first use
init_pool()
