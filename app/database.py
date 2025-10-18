# connect database
from psycopg2 import pool
import os 
from dotenv import load_dotenv
load_dotenv()

DB_PASSWORD = os.getenv("DB_PASSWORD")

print("🔍 Loaded DB_PASS:", "mydbpassword")  # Debug


# Load environment variables (if using dotenv)
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")

# Create a pool of DB connections
db_pool = pool.SimpleConnectionPool(
    minconn=1,   # minimum connections kept open
    maxconn=10,  # maximum connections allowed
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)

# Helper to get a connection
def get_db():
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)
