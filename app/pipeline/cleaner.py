from typing import List, Dict, Any
import re

# Clean and structure the raw text
def clean_structure(prompt: str, raw: List[Any]) -> Dict[str, Any]:
    cleaned = []

    for text in raw:
        # ✅ Skip anything that's not a string
        if not isinstance(text, str):
            continue

        # remove extra spaces
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)

        # normalize
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # remove punctuation

        cleaned.append(text)

    # remove duplicates safely
    unique = list(dict.fromkeys(cleaned))
    combined = "\n\n".join(unique) if unique else "No valid text generated."

    guide = {
        "overview": combined[:300],
        "sections": [
            {"title": "Main Content", "content": combined}
        ],
        "prerequisites": [],
        "extra_tips": [],
        "sources": ["openai", "gemini", "deepseek"]
    }

    return guide
