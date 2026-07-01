import ast
import re
from typing import Any


def is_valid_python(content: str) -> bool:
    if not content or not content.strip():
        return False

    try:
        ast.parse(content)
        return True
    except SyntaxError:
        return False


def extract_python_from_message(message: str) -> str | None:
    if not message:
        return None

    fenced = re.search(
        r"```(?:python)?\s*\n(.*?)```",
        message,
        re.DOTALL | re.IGNORECASE,
    )
    if fenced:
        snippet = fenced.group(1).strip()
        if snippet:
            return snippet

    print_match = re.search(r"(print\s*\((?:[^()]|\([^()]*\))*\))", message)
    if print_match:
        return print_match.group(1).strip()

    after_content = re.search(
        r"เนื้อหา\s+(.+?)(?:\s+แล้ว|\s+และ|\s+ให้|$)",
        message,
        re.IGNORECASE,
    )
    if after_content:
        snippet = after_content.group(1).strip().strip('"').strip("'")
        if snippet:
            return snippet

    return None


def resolve_python_content(
    planned_content: str,
    user_message: str,
) -> tuple[str, dict[str, Any]]:
    metadata: dict[str, Any] = {"content_source": "planner"}

    if is_valid_python(planned_content):
        return planned_content, metadata

    fallback = extract_python_from_message(user_message)
    if fallback and is_valid_python(fallback):
        metadata["content_source"] = "user_message_fallback"
        metadata["planner_content_invalid"] = planned_content
        return fallback, metadata

    return planned_content, metadata
