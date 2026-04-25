from app.schemas import SubjectCreate
from fastapi import HTTPException, APIRouter, Depends
from app.database import get_db

subjects_router = APIRouter()


@subjects_router.post("/create-subject")
def create_subject(subject: SubjectCreate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute(
            """
            INSERT INTO studyguide.subjects (user_id, subject_name)
            VALUES (%s, %s)
            RETURNING subject_id
            """,
            (subject.user_id, subject.subject_name),
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
def get_subjects(user_id: int, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute(
            """
            SELECT subject_id, subject_name, created_at
            FROM studyguide.subjects
            WHERE user_id = %s
            ORDER BY created_at ASC
            """,
            (user_id,),
        )
        subjects = cur.fetchall()
        return [
            {"subject_id": s[0], "subject_name": s[1], "created_at": s[2]}
            for s in subjects
        ]
    finally:
        cur.close()
