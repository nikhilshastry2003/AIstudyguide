# app/pipeline/cleaner.py
from typing import List, Dict, Any
import re
import json

def extract_text_from_raw(raw_text: str) -> str:
    """If string is JSON, attempt to find common fields; else return the string."""
    if not isinstance(raw_text, str):
        # If someone accidentally passed a dict, try to stringify or extract known fields
        try:
            return json.dumps(raw_text)[:2000]
        except Exception:
            return str(raw_text)

    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            # OpenAI-like
            if "choices" in data and isinstance(data["choices"], list):
                msg = data["choices"][0].get("message", {}).get("content")
                if msg:
                    return msg
            # Gemini-like
            if "candidates" in data and isinstance(data["candidates"], list):
                cand = data["candidates"][0]
                # many shapes: cand["content"]["parts"][0]["text"] or cand["content"]["text"]
                try:
                    return cand["content"]["parts"][0]["text"]
                except Exception:
                    pass
                try:
                    return cand.get("text", "")
                except Exception:
                    pass
        # fallback to original string
        return raw_text
    except Exception:
        return raw_text


def clean_structure(prompt: str, raw_texts: List[str]) -> Dict[str, Any]:
    cleaned_texts = []
    for text in raw_texts:
        if not text:
            continue
        piece = extract_text_from_raw(text)
        piece = re.sub(r'\s+', ' ', piece.strip())
        cleaned_texts.append(piece)

    if not cleaned_texts:
        combined = ""
    else:
        # preserve order provided by providers
        combined = "\n\n".join(cleaned_texts)

    overview = (cleaned_texts[0] if cleaned_texts else "No content available..")
    # small sanitization
    overview = re.sub(r'[^\w\s,.\-:]', '', overview).strip()
    if overview and not overview.endswith("."):
        overview = overview + "."

    sections = []
    # if we have multiple provider responses, create a section per provider
    for i, txt in enumerate(cleaned_texts):
        sections.append({"title": f"From {i+1} Provider", "content": txt})

    if not sections:
        sections = [{"title": "Main Content", "content": combined}]

    guide = {
        "overview": overview,
        "sections": sections,
        "prerequisites": [],   # let frontend or later logic fill this
        "extra_tips": [],
        "sources": []
    }

    return guide
