# app/pipeline/call_ai.py
# Call all configured AI providers concurrently, handle errors, and normalize outputs.

import asyncio
from typing import List, Dict, Any

# use absolute import to avoid relative import issues
from app.pipeline.connect_ai import call_openai, call_gemini, call_deepseek, extract_text

async def call_ai(prompt: str) -> List[Dict[str, Any]]:
    """
    Calls all AI providers in parallel and returns a normalized list:
    [
      { "provider": "openai", "model": None, "output_text": "...", "raw": {...}, "error": None },
      ...
    ]
    """
    # list of callables in the same order as providers_list
    tasks = [
        #call_openai(prompt),
        call_gemini(prompt),
        #call_deepseek(prompt),
    ]

    # Run them concurrently and capture exceptions instead of raising (so one failure doesn't kill everything)
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    providers_list = ["openai", "gemini", "deepseek"]
    results: List[Dict[str, Any]] = []

    for provider_name, resp in zip(providers_list, responses):
        # If the provider call raised an exception, record the error and continue
        if isinstance(resp, Exception):
            results.append({
                "provider": provider_name,
                "model": None,
                "output_text": "",
                "raw": {"error": str(resp)},
                "error": str(resp)
            })
            continue

        # resp is expected to be raw JSON/dict from the provider function
        # Normalize: extract text via extract_text() and try to read model if present
        try:
            output_text = extract_text(provider_name, resp) or ""
        except Exception as e:
            # defensive fallback if extractor itself fails
            output_text = ""
            resp = {"error_in_extractor": str(e), "raw": resp}

        # Try to fetch model name from known spots (may not exist)
        model = None
        if isinstance(resp, dict):
            model = resp.get("model") or resp.get("model_name") or None

        results.append({
            "provider": provider_name,
            "model": model,
            "output_text": output_text,
            "raw": resp,
            "error": None
        })

    return results
