"""
Voice Command Processor
Handles intent recognition, language detection, and command parsing.
Uses rule-based NLP (no heavy model needed for submission demo).
"""
import re
from datetime import datetime, timedelta


# ─────────────────────────────────────────────
#  Intent Definitions
# ─────────────────────────────────────────────
INTENTS = {
    "upload": {
        "keywords": ["upload", "add", "import", "send", "अपलोड", "जोड़ें"],
        "response": "Opening upload panel for you.",
    },
    "search": {
        "keywords": ["search", "find", "look", "show me", "get", "खोज", "ढूंढ"],
        "response": "Searching media library...",
    },
    "analytics": {
        "keywords": ["analytics", "stats", "statistics", "report", "performance",
                     "insights", "dashboard", "विश्लेषण", "आँकड़े"],
        "response": "Fetching analytics data for you.",
    },
    "schedule": {
        "keywords": ["schedule", "plan", "set", "remind", "publish at", "निर्धारित"],
        "response": "Opening scheduler panel.",
    },
    "download": {
        "keywords": ["download", "export", "save", "डाउनलोड"],
        "response": "Preparing download.",
    },
    "delete": {
        "keywords": ["delete", "remove", "trash", "हटाएं", "मिटाएं"],
        "response": "Confirm deletion?",
    },
    "play": {
        "keywords": ["play", "open", "view", "watch", "listen", "चलाएं"],
        "response": "Opening media player.",
    },
    "filter": {
        "keywords": ["filter", "category", "type", "sort", "फ़िल्टर"],
        "response": "Applying filter.",
    },
    "help": {
        "keywords": ["help", "what can you do", "commands", "guide", "मदद"],
        "response": "Here are things I can do: upload, search, analytics, schedule, download, delete, play, filter.",
    },
}

# Language keyword map  (simple heuristic – extend as needed)
LANG_HINTS = {
    "hi": ["अपलोड", "जोड़ें", "खोज", "ढूंढ", "विश्लेषण", "आँकड़े",
           "निर्धारित", "डाउनलोड", "हटाएं", "मिटाएं", "चलाएं", "फ़िल्टर", "मदद"],
}


# ─────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────
def process_voice_command(text: str) -> dict:
    """
    Main entry point.
    Returns a structured result dict consumed by the Flask route.
    """
    if not text or not text.strip():
        return _error_result("Empty command received.")

    text_clean = text.strip()
    language   = _detect_language(text_clean)
    intent, confidence = _detect_intent(text_clean)
    entities   = _extract_entities(text_clean)
    response   = INTENTS.get(intent, {}).get("response", "Command received.")

    return {
        "raw_text":       text_clean,
        "detected_intent": intent,
        "language":       language,
        "confidence":     confidence,
        "entities":       entities,
        "response_text":  response,
        "success":        True,
        "timestamp":      datetime.utcnow().isoformat(),
    }


def get_available_commands() -> list:
    """Return all supported command categories with examples."""
    examples = {
        "upload":    ["upload a video", "add new image", "import file"],
        "search":    ["search tutorial videos", "find marketing images"],
        "analytics": ["show analytics", "get performance report", "open dashboard"],
        "schedule":  ["schedule publish tomorrow", "set task for next week"],
        "download":  ["download the report", "export analytics"],
        "delete":    ["delete file", "remove old video"],
        "play":      ["play the podcast", "open the video"],
        "filter":    ["filter by video", "sort by category"],
        "help":      ["help", "what can you do"],
    }
    return [
        {"intent": k, "examples": examples.get(k, []), "keywords": v["keywords"][:4]}
        for k, v in INTENTS.items()
    ]


# ─────────────────────────────────────────────
#  Private Helpers
# ─────────────────────────────────────────────
def _detect_language(text: str) -> str:
    for lang, hints in LANG_HINTS.items():
        if any(h in text for h in hints):
            return lang
    # Fallback: check unicode ranges
    if re.search(r'[\u0900-\u097F]', text):   # Devanagari
        return "hi"
    return "en"


def _detect_intent(text: str) -> tuple:
    text_lower = text.lower()
    best_intent = "unknown"
    best_score  = 0.0

    for intent, data in INTENTS.items():
        score = 0.0
        for kw in data["keywords"]:
            if kw.lower() in text_lower:
                # Longer keyword → more specific match → higher weight
                weight = len(kw.split()) * 0.15 + 0.70
                score = max(score, min(weight, 0.99))
        if score > best_score:
            best_score  = score
            best_intent = intent

    # Boost confidence if only one keyword matched exactly
    if best_score == 0.0:
        best_intent = "unknown"
        best_score  = 0.30

    return best_intent, round(best_score, 2)


def _extract_entities(text: str) -> dict:
    """Extract file types, categories, dates from command text."""
    entities = {}

    # File type
    types = ["video", "image", "audio", "document", "pdf", "mp4", "mp3", "png", "jpg"]
    for t in types:
        if t in text.lower():
            entities["file_type"] = t
            break

    # Category
    cats = ["marketing", "education", "entertainment", "news", "sports"]
    for c in cats:
        if c in text.lower():
            entities["category"] = c
            break

    # Relative date hints
    now = datetime.utcnow()
    if "today" in text.lower():
        entities["date"] = now.strftime("%Y-%m-%d")
    elif "tomorrow" in text.lower():
        entities["date"] = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "next week" in text.lower():
        entities["date"] = (now + timedelta(weeks=1)).strftime("%Y-%m-%d")
    elif "next month" in text.lower():
        entities["date"] = (now + timedelta(days=30)).strftime("%Y-%m-%d")

    # Number extraction (e.g. "show top 5")
    nums = re.findall(r'\b(\d+)\b', text)
    if nums:
        entities["number"] = int(nums[0])

    return entities


def _error_result(msg: str) -> dict:
    return {
        "raw_text": "",
        "detected_intent": "unknown",
        "language": "en",
        "confidence": 0.0,
        "entities": {},
        "response_text": msg,
        "success": False,
        "timestamp": datetime.utcnow().isoformat(),
    }
