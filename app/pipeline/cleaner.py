# app/pipeline/cleaner.py
from typing import List, Dict, Any
import re
import json

def extract_text_from_raw(raw_text: str) -> str:
    """Extracts readable content from any mock JSON or text."""
    try:
        # Try to load as JSON
        data = json.loads(raw_text)
        if isinstance(data, dict):
            # Gemini / OpenAI style
            if "choices" in data and isinstance(data["choices"], list):
                content = data["choices"][0].get("message", {}).get("content")
                if content:
                    return content
        return raw_text
    except Exception:
        # Not JSON, just return as text
        return raw_text

def clean_structure(prompt: str, raw_texts: List[str]) -> Dict[str, Any]:
    """
    Takes raw provider outputs, extracts readable content, cleans it, and structures it.
    """

    #Extract and clean readable parts
    cleaned_texts = []
    for text in raw_texts:
        if not text:
            continue
        extracted = extract_text_from_raw(text)
        cleaned = re.sub(r'\s+', ' ', extracted.strip())
        cleaned_texts.append(cleaned)

    combined = "\n\n".join(cleaned_texts)

    # Create overview (first line)
    overview = cleaned_texts[0] if cleaned_texts else "No content available."
    overview = re.sub(r'[^\w\s,.]', '', overview)
    overview = overview.strip() + "."

    # ✅ Simple section splitting
    sections = [{"title": f"From {i+1} Provider", "content": txt} for i, txt in enumerate(cleaned_texts)]

    # Build final structured guide
    guide = {
        "overview": overview,
        "sections": sections or [{"title": "Main Content", "content": combined}],
        "prerequisites": [f"Basic understanding of {prompt.split()[0]}", "General computer knowledge"],
        "extra_tips": [
            "Try relating this concept to a real database you’ve seen (like MySQL or MongoDB).",
            "Sketch a simple diagram of how this fits into a data system."
        ],
        "sources": ["openai", "gemini", "deepseek"]
    }

    return guide
