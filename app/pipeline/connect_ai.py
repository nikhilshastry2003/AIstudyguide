# app/pipeline/connect_ai.py
# Connectors to external AI providers (OpenAI, Gemini, DeepSeek).
# Returns raw provider JSON so the normalizer / extractor can handle it.

import os
import json
from dotenv import load_dotenv
import httpx

load_dotenv()

# Use clear env names. Accept both older names and new ones for convenience.
OPENAI_API = os.getenv("OPENAI_API") or os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
DEEPSEEK_API = os.getenv("DEEPSEEK_API") or os.getenv("DEEPSEEK_API_KEY")

# -----------------------------
# OpenAI connector (async)
# -----------------------------
async def call_openai(prompt: str) -> dict:
    if not OPENAI_API:
        # Mock so dev flow continues without API keys
        return {"mock": True, "provider": "openai", "choices": [{"message": {"content": "MOCK OpenAI answer for: " + prompt}}]}

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # Return raw JSON — extractor will pick out the useful bits
    print("🔍 OPENAI RAW:", json.dumps(data, indent=2)[:1000])
    return data



# Gemini connector (async)
# Notes:
# - Use GEMINI_API_KEY env variable name (commonly used).
# - Use the v1beta models/{model}:generateContent endpoint (model string must be correct).
# - Some Google Generative API shapes place text in "candidates" or "candidates[0].content.parts".

async def call_gemini(prompt: str) -> dict:
    api_key = os.getenv("GEMINI_API")
    if not api_key:
        return {
            "mock": True,
            "provider": "gemini",
            "candidates": [{
                "content": {"parts": [{"text": "MOCK Gemini answer for: " + prompt}]}
            }]
        }

    # Correct model name
    model = "gemini-2.5-pro"

    # ❗ FINAL CORRECT ENDPOINT (v1beta)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    params = {"key": api_key}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, params=params, json=payload)
        resp.raise_for_status()
        data = resp.json()

    print("🔍 GEMINI RAW:", json.dumps(data, indent=2)[:2000])
    return data



# DeepSeek connector (async)

async def call_deepseek(prompt: str) -> dict:
    if not DEEPSEEK_API:
        return {"mock": True, "provider": "deepseek", "choices": [{"message": {"content": "MOCK DeepSeek answer for: " + prompt}}]}

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    print("🔍 DEEPSEEK RAW:", json.dumps(data, indent=2)[:1000])
    return data



# Defensive extractor for raw provider JSON

def extract_text(provider: str, data: dict) -> str:
    """
    Try several known shapes and return the best text. If nothing found,
    return either a JSON-string preview or ''.
    """
    if not isinstance(data, dict):
        return str(data or "")

    provider_key = provider.lower()

    # OpenAI chat completion shape
    if provider_key == "openai":
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        try:
            return data["choices"][0]["text"].strip()
        except Exception:
            pass

    # Gemini candidate style
    if provider_key == "gemini":
        # Google generative API often returns 'candidates' with nested content.parts
        try:
            # new style: candidates -> content -> parts -> text
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass
        try:
            # older/alternate shapes
            return data["candidates"][0]["text"].strip()
        except Exception:
            pass
        try:
            # sometimes payload is under 'output'
            return data["output"][0]["text"].strip()
        except Exception:
            pass

    # Deepseek and other openai-like shapes
    if provider_key == "deepseek":
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        try:
            return data["choices"][0]["text"].strip()
        except Exception:
            pass

    # Generic fallback fields
    for key in ("text", "content", "message"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()

    # Pretty-print small JSON preview as last resort
    try:
        return json.dumps(data)[:2000]
    except Exception:
        return ""
