from fastapi import HTTPException, APIRouter, Depends
from app.schemas import SessionCreate
from app.database import get_db

sessions_router = APIRouter()


@sessions_router.post("/create-session")
def create_session(session: SessionCreate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute(
            """
            INSERT INTO studyguide.sessions (subject_id, title)
            VALUES (%s, %s)
            RETURNING session_id
            """,
            (session.subject_id, session.title),
        )
        session_id = cur.fetchone()[0]
        db.commit()
        return {"session_id": session_id, "message": "Session created successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()


@sessions_router.get("/my-sessions/{subject_id}")
def get_sessions(subject_id: int, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute(
            """
            SELECT session_id, title, created_at
            FROM studyguide.sessions
            WHERE subject_id = %s
            ORDER BY created_at ASC
            """,
            (subject_id,),
        )
        sessions = cur.fetchall()
        return [
            {"session_id": s[0], "title": s[1], "created_at": s[2]}
            for s in sessions
        ]
    finally:
        cur.close()
