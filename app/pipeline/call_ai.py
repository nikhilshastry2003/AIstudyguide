# app/pipeline/call_ai.py
import asyncio
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
load_dotenv()

from app.pipeline.connect_ai import call_openai, call_gemini, call_deepseek, extract_text

async def call_ai(prompt: str) -> List[Dict[str, Any]]:
    """
    Run only the providers for which an API key exists (or their mock).
    Returns normalized list of dicts:
      { provider, model, output_text, raw, error }
    """
    tasks = []
    providers = []

    if os.getenv("OPENAI_API"):
        tasks.append(call_openai(prompt))
        providers.append("openai")

    if os.getenv("GEMINI_API"):
        tasks.append(call_gemini(prompt))
        providers.append("gemini")

    if os.getenv("DEEPSEEK_API"):
        tasks.append(call_deepseek(prompt))
        providers.append("deepseek")

    if not tasks:
        # No keys available — return empty so pipeline can still run (or you could raise)
        return []

    # execute concurrently, capture exceptions
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    results: List[Dict[str, Any]] = []
    for provider_name, resp in zip(providers, responses):
        print(f"Calling provider: {provider_name}")
        print("Raw Response (truncated):", str(resp)[:1000])

        if isinstance(resp, Exception):
            results.append({
                "provider": provider_name,
                "model": None,
                "output_text": "",
                "raw": {"error": str(resp)},
                "error": str(resp)
            })
            continue

        # Normalize text via extractor
        output_text = extract_text(provider_name, resp) or ""
        model = resp.get("model") if isinstance(resp, dict) else None

        results.append({
            "provider": provider_name,
            "model": model,
            "output_text": output_text,
            "raw": resp,
            "error": None
        })

    return results
