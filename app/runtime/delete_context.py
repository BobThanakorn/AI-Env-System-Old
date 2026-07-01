import re
from pathlib import Path
from typing import Any

from app.core.config import WORKSPACE_DIR
from app.tools.file_tools import safe_path

DELETE_INTENT_PATTERN = re.compile(
    r"(ลบ(?:ไฟล์)?|delete(?:\s+file)?|remove(?:\s+file)?|erase(?:\s+file)?)",
    re.IGNORECASE,
)

DELETE_PATH_PATTERN = re.compile(
    r"(?:ลบ(?:ไฟล์)?|delete(?:\s+file)?|remove(?:\s+file)?)\s+[`'\"]?([^\s`\"']+)",
    re.IGNORECASE,
)


def message_requests_delete(message: str) -> bool:
    return bool(DELETE_INTENT_PATTERN.search(message))


def extract_delete_path(message: str) -> str | None:
    match = DELETE_PATH_PATTERN.search(message.strip())
    if not match:
        return None

    path = match.group(1).strip().strip("`").strip('"').strip("'")
    return path or None


def resolve_workspace_file_path(path: str) -> str | None:
    normalized = path.replace("\\", "/").strip().lstrip("/")
    if not normalized:
        return None

    candidates = [normalized]
    filename = Path(normalized).name

    if "/" not in normalized:
        candidates.extend(
            [
                f"scripts/{filename}",
                f"notes/{filename}",
            ]
        )

    for candidate in candidates:
        try:
            target = safe_path(candidate)
        except ValueError:
            continue

        if target.exists() and target.is_file():
            return candidate

    return normalized


def build_delete_fallback_plan(path: str) -> dict[str, Any]:
    resolved = resolve_workspace_file_path(path) or path
    return {
        "action": "delete_file",
        "args": {"path": resolved},
        "reason": "User asked to delete a workspace file",
    }
