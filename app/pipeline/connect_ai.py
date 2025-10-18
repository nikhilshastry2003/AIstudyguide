# app/pipeline/connect_ai.py
# Connectors to external AI providers (OpenAI, Gemini, DeepSeek).
# These functions return the raw provider response (dict) so the caller
# can normalize / extract text in one place.

import os
import json
from dotenv import load_dotenv
import httpx
import requests
load_dotenv()

# Read keys from .env. Use clear names (match your .env).
OPENAI_API = os.getenv("OPENAI_API")
GEMINI_API = os.getenv("GEMINI_API")
DEEPSEEK_API = os.getenv("DEEPSEEK_API")


# -----------------------------
# OpenAI connector
# -----------------------------
async def call_openai(prompt: str) -> dict:
    """
    Calls OpenAI Chat Completions endpoint and returns the parsed JSON.
    If API key missing, return a small mock for local testing.
    """
    if not OPENAI_API:
        # Return a simple mock response so pipeline runs during dev/testing
        return {"mock": True, "provider": "openai", "choices": [{"message": {"content": "MOCK OpenAI answer for: " + prompt}}]}

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4",                       # change as needed
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        # raise for HTTP errors (so caller receives an Exception which call_ai will handle)
        resp.raise_for_status()
        data = resp.json()

    # Helpful debug log (safe to remove later)
    print("🔍 OPENAI RAW:", json.dumps(data, indent=2)[:2000])  # limit output
    return data


# -----------------------------
# Gemini connector
# -----------------------------
def call_gemini(prompt: str):
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    return result

# -----------------------------
# DeepSeek connector
# -----------------------------
async def call_deepseek(prompt: str) -> dict:
    """
    Calls DeepSeek (example) — update endpoint if provider uses a different path.
    If API key missing, return a mock.
    """
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

    print("🔍 DEEPSEEK RAW:", json.dumps(data, indent=2)[:2000])
    return data


# -----------------------------
# Utility: extract_text
# -----------------------------
def extract_text(provider: str, data: dict) -> str:
    """
    Defensive extractor for provider responses. Tries common response shapes.
    Returns the best text found (or empty string).
    Keep this small & extend later if you see new raw shapes in logs.
    """
    if not isinstance(data, dict):
        return str(data or "")

    provider = provider.lower()
    # OpenAI chat-style
    if provider == "openai":
        # common shapes: choices[0].message.content or choices[0].text
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        try:
            return data["choices"][0]["text"].strip()
        except Exception:
            pass

    # Gemini style (candidate parts)
    if provider == "gemini":
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass
        try:
            # alternative shapes
            return data["output"][0]["text"].strip()
        except Exception:
            pass

    # DeepSeek / OpenAI-like fallback
    if provider == "deepseek":
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        try:
            return data["choices"][0]["text"].strip()
        except Exception:
            pass

    # Generic fallback: look for any likely text field
    for key in ("text", "content", "message"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()

    # Last resort: return truncated JSON string so you at least see something
    try:
        return json.dumps(data)[:2000]
    except Exception:
        return ""
