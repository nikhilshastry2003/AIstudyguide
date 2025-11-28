import asyncio
import json
import time
from typing import Any, Dict, List, Optional

from app.pipeline.call_ai import call_ai         # Calls all AI providers asynchronously
from app.pipeline.cleaner import clean_structure # Cleans and structures raw AI outputs

from app import database                        # For DB connection pooling (db_pool)
import psycopg2
import psycopg2.extras

# For small projects, explicit threadpool offloading not required for DB ops.
# For high concurrency, consider starlette.concurrency.run_in_threadpool for blocking DB ops.

async def run_pipeline(prompt: str, user_id: Optional[int] = None, session_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Orchestrates the end-to-end workflow of generating a structured guide from AI providers.
    Steps:
      1. Insert a 'job' row in DB with status 'running'
      2. Call AI providers asynchronously
      3. Save raw provider outputs in DB
      4. Clean/structure all outputs into a user-facing guide
      5. Save guide in DB
      6. Update job status to 'done'
      7. Return results for client
    """
    conn = None
    cur = None
    job_id = None
    try:
        # Get a DB connection from the pool (recommended for performance)
        conn = database.db_pool.getconn()
        cur = conn.cursor()

        # Step 1: Insert a new job record (marks status as 'running')
        cur.execute(
            """
            INSERT INTO pipeline.jobs (user_id, session_id, prompt, status)
            VALUES (%s, %s, %s, %s)
            RETURNING job_id
            """,
            ((user_id if user_id and user_id > 0 else None, session_id, prompt, "running"))
        )
        job_id = cur.fetchone()[0]
        conn.commit()  # Ensure job row exists even if AI calls fail later

        # Step 2: Asynchronously call all configured AI providers
        t0 = time.time()
        provider_outputs = await call_ai(prompt)  # List[dict] from call_ai
        # Normalize outputs: always a list of dicts for downstream consistency
        if isinstance(provider_outputs, dict):
            provider_list = [
                {**payload, "provider": prov}
                if isinstance(payload, dict) else {"provider": prov, "text": payload}
                for prov, payload in provider_outputs.items()
            ]
        else:
            provider_list = provider_outputs

        # Step 3: Save all provider outputs into the DB
        for po in provider_list:
            provider = po.get("provider", "unknown")
            model = po.get("model")
            output_text = po.get("output_text") or po.get("text")
            output_json = po.get("raw") or po
            tokens_used = po.get("tokens")
            latency_ms = po.get("latency_ms", int((time.time() - t0) * 1000))
            error = po.get("error")

            # Store output as JSONB for easy querying later
            try:
                cur.execute(
                    """
                    INSERT INTO pipeline.provider_outputs
                        (job_id, provider, model, output_json, output_text, tokens_used, latency_ms, error)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        job_id,
                        provider,
                        model,
                        json.dumps(output_json) if output_json is not None else None,
                        output_text,
                        tokens_used,
                        latency_ms,
                        error,
                    ),
                )
            except Exception as e:
                # Log provider-specific save errors, but continue (robust)
                conn.rollback()
                cur.execute(
                    "UPDATE pipeline.jobs SET error = COALESCE(error, '') || %s || E'\\n' WHERE job_id = %s",
                    (f"provider_save_error ({provider}): {str(e)}", job_id),
                )
                conn.commit()

        conn.commit()

        # Step 4: Prepare for guide cleaning: only add non-empty outputs
        raw_texts = []
        for po in provider_list:
            text = po.get("output_text") or po.get("text") or ""
            if text and isinstance(text, str) and text.strip():
                raw_texts.append(text)
        print("🧠 DEBUG raw_texts:", raw_texts, type(raw_texts))

        guide = clean_structure(prompt, raw_texts)  # Clean and structure guide
        print("🧠 DEBUG guide:", guide)

        # Step 5: Save final guide in DB (JSON string in pipeline.guides)
        guide_json_str = json.dumps(guide)
        guide_summary = (guide.get("overview") or "")[:1000]  # Up to 1k chars

        cur.execute(
            """
            INSERT INTO pipeline.guides (job_id, user_id, session_id, guide_json, summary)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING guide_id
            """,
            (job_id, user_id, session_id, guide_json_str, guide_summary),
        )
        guide_id = cur.fetchone()[0]
        conn.commit()

        # Step 6: Mark job 'done', attach guide
        cur.execute(
            "UPDATE pipeline.jobs SET status = %s, result_guide_id = %s, updated_at = NOW() WHERE job_id = %s",
            ("done", guide_id, job_id),
        )
        conn.commit()

        # Step 7: Add source info for transparency
        guide["sources"] = [
            {
                "provider": po.get("provider", "unknown"),
                "model": po.get("model"),
                "snippet": (po.get("output_text") or po.get("text") or "")[:300],
            }
            for po in provider_list
        ]

        return {"job_id": job_id, "guide": guide, "provider_outputs": provider_list}

    except Exception as e:
        # Failure: update job status, persist error, re-raise for HTTP error response
        try:
            if conn and job_id:
                cur.execute(
                    "UPDATE pipeline.jobs SET status=%s, error=%s, updated_at=NOW() WHERE job_id=%s",
                    ("failed", str(e), job_id),
                )
                conn.commit()
        except Exception:
            if conn:
                conn.rollback()
        raise  # Let FastAPI surface error

    finally:
        # Always close DB resources (avoids leaks)
        try:
            if cur:
                cur.close()
        finally:
            if conn:
                database.db_pool.putconn(conn)
