from fastapi import FastAPI, HTTPException, APIRouter, Depends
from app.schemas import UserCreate , UserLogin
from passlib.context import CryptContext
from app.database import get_db
import psycopg2

auth_router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@auth_router.post("/signup")
def signup(user: UserCreate, db=Depends(get_db)):
    """Create a new user in the system.
    Steps:
    1. Hash the password for security.
    2. Insert user into PostgreSQL.
    3. Return user_id if successful, error if email exists.
    """
    hashed_password = pwd_context.hash(user.password)
    
    cur = db.cursor()
    try:
        cur.execute(
            """
            INSERT INTO studyguide.users (name, email, password)
            VALUES (%s, %s, %s)
            RETURNING user_id
            """,
            (user.name, user.email, hashed_password)
        )
        user_id = cur.fetchone()[0]
        db.commit()
        return {"user_id": user_id, "message": "User created successfully"}
    
    except psycopg2.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    finally:
        cur.close()
        

        
@auth_router.post("/login")
def login(user: UserLogin,db=Depends(get_db) ):
    """
    Steps:
    1. Fetch user by email from DB.
    2. Compare hashed password.
    3. Return success if correct, error if not.
    """
    cur = db.cursor()
    try:
        cur.execute("SELECT user_id, password FROM studyguide.users WHERE email = %s", (user.email,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=400, detail="Email not registered")

        user_id, hashed_password = result

        if not pwd_context.verify(user.password, hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect password")

        return {"user_id": user_id, "message": "Login successful"}

    finally:
        cur.close()