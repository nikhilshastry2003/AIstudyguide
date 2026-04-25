from fastapi import HTTPException, APIRouter, Depends
from app.schemas import ChatCreate
from app.database import get_db

chats_router = APIRouter()


@chats_router.post("/submit-prompt")
def submit_prompt(chat: ChatCreate, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute(
            """
            INSERT INTO studyguide.chats (session_id, question)
            VALUES (%s, %s)
            RETURNING chat_id
            """,
            (chat.session_id, chat.question),
        )
        chat_id = cur.fetchone()[0]
        db.commit()

        ai_response = f"Mock AI answer for: {chat.question}"

        cur.execute(
            "UPDATE studyguide.chats SET answer = %s WHERE chat_id = %s",
            (ai_response, chat_id),
        )
        db.commit()

        return {"chat_id": chat_id, "question": chat.question, "answer": ai_response}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()


@chats_router.get("/my-chats/{session_id}")
def get_chats(session_id: int, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute(
            """
            SELECT chat_id, question, answer, created_at
            FROM studyguide.chats
            WHERE session_id = %s
            ORDER BY created_at ASC
            """,
            (session_id,),
        )
        chats = cur.fetchall()
        return [
            {"chat_id": c[0], "question": c[1], "answer": c[2], "created_at": c[3]}
            for c in chats
        ]
    finally:
        cur.close()
