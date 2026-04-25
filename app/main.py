from fastapi import FastAPI
from app.routers import auth, chats, resource, subjects, sessions, pipeline_router
from app.database import init_db_pool
from dotenv import load_dotenv
import os

load_dotenv()

print("✅ OpenAI:", os.getenv("OPENAI_API") is not None)
print("✅ Gemini:", os.getenv("GEMINI_API") is not None)
print("✅ DeepSeek:", os.getenv("DEEPSEEK_API") is not None)

app = FastAPI()

app.include_router(auth.auth_router)
app.include_router(chats.chats_router)
app.include_router(resource.resource_router)
app.include_router(subjects.subjects_router)
app.include_router(sessions.sessions_router)
app.include_router(pipeline_router.pipeline_router)


@app.on_event("startup")
def startup_event():
    try:
        init_db_pool()
        from app.database import db_pool as _pool
        conn = _pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.close()
        _pool.putconn(conn)
        print("✅ Database connection successful.")
    except Exception as e:
        print("❌ Database connection failed:", e)


@app.on_event("shutdown")
def shutdown_event():
    from app.database import db_pool as _pool
    if _pool:
        _pool.closeall()
        print("✅ Database connections closed.")
