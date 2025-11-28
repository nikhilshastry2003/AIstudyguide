# app/routers/pipeline_router.py
from fastapi import APIRouter, HTTPException
from app.schemas import JobCreate
from app.pipeline.orchestrator import run_pipeline
from typing import Any

pipeline_router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

@pipeline_router.post("/run")
async def run_endpoint(job: JobCreate):
    """
    Body: { "user_id": 1, "prompt": "..." }
    Ensures we pass None for user_id if the provided id is not a positive int
    (to avoid FK violation with value 0).
    """
    print("📩 Received request:", job.dict())
    user_id = getattr(job, "user_id", None)
    # Normalize invalid user id values -> None (so DB will store NULL)
    try:
        user_id_int = int(user_id) if user_id is not None else None
    except Exception:
        user_id_int = None

    if user_id_int is not None and user_id_int <= 0:
        user_id_int = None

    prompt = job.prompt

    try:
        result = await run_pipeline(prompt, user_id=user_id_int)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "user_id": user_id_int,
        "prompt": prompt,
        "guide": result.get("guide"),
        "provider_outputs": result.get("provider_outputs"),
    }
