# connect database
from psycopg2 import pool
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")

db_pool = None

def init_db_pool():
    global db_pool
    db_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )

def get_db():
    if db_pool is None:
        raise RuntimeError("Database is not available")
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)
