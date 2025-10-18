from app.schemas import SubjectCreate, SessionCreate
from fastapi import FastAPI, HTTPException, APIRouter, Depends
from app.schemas import UserCreate , UserLogin
from passlib.context import CryptContext
from app.database import get_db
import psycopg2

subjects_router = APIRouter()
@subjects_router.post("/create-subject")
def create_subject(subject: SubjectCreate, db=Depends(get_db)):
    """
    Create a new subject for a user.
    """
    cur = db.cursor()
    try:
        cur.execute(
            """
            INSERT INTO studyguide.subjects (user_id, subject_name)
            VALUES (%s, %s)
            RETURNING subject_id
            """,
            (subject.user_id, subject.subject_name)
        )
        subject_id = cur.fetchone()[0]
        db.commit()
        return {"subject_id": subject_id, "message": "Subject created successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        cur.close()

@subjects_router.get("/my-subjects/{user_id}")
def get_subjects(user_id: int,db=Depends(get_db)):
    """
    Fetch all subjects created by a given user.
    """
    cur = db.cursor()
    try:
        cur.execute(
            """
            SELECT subject_id, name, created_at
            FROM studyguide.subjects
            WHERE user_id = %s
            ORDER BY created_at ASC
            """,
            (user_id,)
        )
        subjects = cur.fetchall()
        return [
            {"subject_id": s[0], "name": s[1], "created_at": s[2]}
            for s in subjects
        ]
    finally:
        cur.close()