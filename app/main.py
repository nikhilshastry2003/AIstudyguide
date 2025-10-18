from fastapi import FastAPI
from app.database import db_pool 

# Import routers from your existing ones
from app.routers import auth, chats, resource, subjects, sessions , pipeline_router
from app.pipeline.orchestrator import run_pipeline
from dotenv import load_dotenv
import os

load_dotenv()

print("✅ OpenAI:", os.getenv("OPENAI_API") is not None)
print("✅ Gemini:", os.getenv("GEMINI_API") is not None)
print("✅ DeepSeek:", os.getenv("DEEPSEEK_API") is not None)

app = FastAPI()

# Register routers
app.include_router(auth.auth_router)
app.include_router(chats.chats_router)
app.include_router(resource.resource_router)
app.include_router(subjects.subjects_router)
app.include_router(sessions.sessions_router)
app.include_router(pipeline_router.pipeline_router)

# Startup event → test DB connection
@app.on_event("startup")
def startup_event():
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")  # quick test query
        cursor.close()
        db_pool.putconn(conn)
        print("✅ Database connection successful.")
    except Exception as e:
        print("❌ Database connection failed:", e)
        raise e

# Shutdown event → close DB pool
@app.on_event("shutdown")
def shutdown_event():
    if db_pool:
        db_pool.closeall()
        print("✅ Database connections closed.")
