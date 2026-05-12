import json
from typing import Optional


def extract_json_str(text: str) -> Optional[str]:
    """Return the first top-level JSON object in `text` as a raw string.

    Uses balanced-brace scanning to correctly handle `}` inside string values.
    Returns None if no complete JSON object is found.
    """
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse_json_object(text: str) -> dict:
    """Extract and parse the first JSON object from `text`.

    Raises:
        ValueError: if no JSON object is found or the JSON is invalid.
    """
    raw = extract_json_str(text)
    if raw is None:
        raise ValueError("No JSON object found in model response")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in model response: {exc}") from exc
