# routers/pipeline_router.py
from fastapi import APIRouter, HTTPException
from app.schemas import JobCreate
from app.pipeline.orchestrator import run_pipeline   # import orchestrator (async)
from typing import List, Dict, Any
# Export router as pipeline_router so main.py can import it consistently
pipeline_router = APIRouter(prefix="/pipeline", tags=["Pipeline"])
    
@pipeline_router.post("/run")
async def run_endpoint(job: JobCreate):
    print("📩 Received request:", job.dict())
    """
    POST /pipeline/run
    Body: { "user_id": 1, "prompt": "..." }
    """
    user_id = getattr(job, "user_id", None)
    prompt = job.prompt

    try:
        # run_pipeline is async — await it
        result = await run_pipeline(prompt, user_id=user_id)
    except Exception as e:
        # Turn internal errors into a controlled HTTP error
        raise HTTPException(status_code=500, detail=str(e))

    # Return keys using result.get(...) safely
    return {
        "user_id": user_id,
        "prompt": prompt,
        "guide": result.get("guide"),
        "provider_outputs": result.get("provider_outputs")
    }
