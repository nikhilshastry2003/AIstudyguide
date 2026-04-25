from fastapi import HTTPException, APIRouter, Depends
from app.schemas import UserCreate, UserLogin
from app.database import get_db
from passlib.context import CryptContext
import psycopg2

auth_router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@auth_router.post("/signup")
def signup(user: UserCreate, db=Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    cur = db.cursor()
    try:
        cur.execute(
            """
            INSERT INTO studyguide.users (name, email, password)
            VALUES (%s, %s, %s)
            RETURNING user_id
            """,
            (user.name, user.email, hashed_password),
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
def login(user: UserLogin, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute(
            "SELECT user_id, password FROM studyguide.users WHERE email = %s",
            (user.email,),
        )
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        user_id, hashed_password = result

        if not pwd_context.verify(user.password, hashed_password):
            raise HTTPException(status_code=400, detail="Invalid credentials")

        return {"user_id": user_id, "message": "Login successful"}

    finally:
        cur.close()
