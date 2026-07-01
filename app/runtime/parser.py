import json
from typing import Any


def extract_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)

    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end <= start:
            return {
                "action": "answer",
                "args": {},
                "reason": "Could not parse JSON, answer directly",
            }

        try:
            return json.loads(text[start:end])

        except json.JSONDecodeError:
            return {
                "action": "answer",
                "args": {},
                "reason": "Invalid JSON from model, answer directly",
            }
