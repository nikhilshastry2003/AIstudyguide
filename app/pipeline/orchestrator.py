# app/pipeline/orchestrator.py

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

from app.pipeline.call_ai import call_ai   # your async function that queries providers
from app.pipeline.cleaner import clean_structure    # your cleaner that returns a guide dict

from app import database  # expects app.database.db_pool to exist
import psycopg2
import psycopg2.extras

# NOTE: this orchestrator uses blocking DB calls via psycopg2.
# For high-concurrency production you should run DB work in a threadpool
# (e.g., starlette.concurrency.run_in_threadpool). For learning and small load this is fine.

async def run_pipeline(prompt: str, user_id: Optional[int] = None, session_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Full pipeline flow:
      1) Insert a job row (status running)
      2) Call AI providers (parallel)
      3) Save provider outputs
      4) Clean & structure outputs (guide)
      5) Save guide
      6) Update job status -> done
    Returns: {"job_id": ..., "guide": {...}, "provider_outputs": [...]}
    """

    conn = None
    cur = None
    job_id = None
    try:
        # 0) Get a DB connection from the pool
        conn = database.db_pool.getconn()
        cur = conn.cursor()

        # 1) Create a job row with status 'running'
        cur.execute(
            """
            INSERT INTO pipeline.jobs (user_id, session_id, prompt, status)
            VALUES (%s, %s, %s, %s)
            RETURNING job_id
            """,
            (user_id, session_id, prompt, "running")
        )
        job_id = cur.fetchone()[0]
        conn.commit()  # commit so job row exists even if next steps fail

        # 2) Call AI providers (async): this returns dict or list of outputs
        t0 = time.time()
        provider_outputs = await call_ai(prompt)  # await your async call_all_models
        # Normalize to list of dicts
        if isinstance(provider_outputs, dict):
            # convert mapping provider -> payload to list preserving provider key in payload
            provider_list: List[Dict[str, Any]] = []
            for prov, payload in provider_outputs.items():
                # ensure payload is a dict that contains provider name/model/text keys
                if isinstance(payload, dict):
                    payload.setdefault("provider", prov)
                    provider_list.append(payload)
                else:
                    provider_list.append({"provider": prov, "text": payload})
        else:
            provider_list = provider_outputs  # assume it's already a list

        # 3) Save provider outputs into pipeline.provider_outputs
        for po in provider_list:
            provider = po.get("provider") or po.get("provider_name") or "unknown"
            model = po.get("model")
            output_text = po.get("output_text") or po.get("text") or None
            output_json = po.get("raw") or po.get("output_json") or po  # store raw dict if present
            tokens_used = po.get("tokens") or None
            latency_ms = po.get("latency_ms") or int((time.time() - t0) * 1000)
            error = po.get("error") or None

            # store JSONB content as json.dumps(...) or with psycopg2.extras.Json
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
                        error
                    )
                )
            except Exception as e:
                # don't fail whole pipeline if one provider output can't be saved, just record error
                conn.rollback()
                cur.execute(
                    "UPDATE pipeline.jobs SET error = COALESCE(error, '') || %s || E'\\n' WHERE job_id = %s",
                    (f"provider_save_error ({provider}): {str(e)}", job_id)
                )
                conn.commit()

        conn.commit()

        # 4) Collect texts and run cleaner
        raw_texts: List[str] = []
        for po in provider_list:
            text = po.get("output_text") or po.get("text") or ""
            if isinstance(text, str) and text.strip():
                raw_texts.append(text)
                
        print("🧠 DEBUG raw_texts:", raw_texts, type(raw_texts))


        guide = clean_structure(prompt, raw_texts)
        print("🧠 DEBUG guide:", guide)


        # 5) Save final guide into pipeline.guides
        guide_json_str = json.dumps(guide)
        guide_summary = (guide.get("overview") or "")[:1000]  # short summary

        cur.execute(
            """
            INSERT INTO pipeline.guides (job_id, user_id, session_id, guide_json, summary)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING guide_id
            """,
            (job_id, user_id, session_id, guide_json_str, guide_summary)
        )
        guide_id = cur.fetchone()[0]
        conn.commit()

        # 6) Update job row to done and link guide
        cur.execute(
            "UPDATE pipeline.jobs SET status = %s, result_guide_id = %s, updated_at = NOW() WHERE job_id = %s",
            ("done", guide_id, job_id)
        )
        conn.commit()

        # attach computed metadata
        guide["sources"] = [
            {
                "provider": po.get("provider") or "unknown",
                "model": po.get("model"),
                "snippet": (po.get("output_text") or po.get("text") or "")[:300]
            }
            for po in provider_list
        ]

        # 7) Return results
        return {"job_id": job_id, "guide": guide, "provider_outputs": provider_list}

    except Exception as e:
        # Mark job as failed and save error message if job exists
        try:
            if conn and job_id:
                cur.execute(
                    "UPDATE pipeline.jobs SET status=%s, error=%s, updated_at=NOW() WHERE job_id=%s",
                    ("failed", str(e), job_id)
                )
                conn.commit()
        except Exception:
            if conn:
                conn.rollback()

        raise  # re-raise to let the caller (FastAPI route) convert to HTTP error

    finally:
        # Always cleanup DB resources
        try:
            if cur:
                cur.close()
        finally:
            if conn:
                database.db_pool.putconn(conn)
