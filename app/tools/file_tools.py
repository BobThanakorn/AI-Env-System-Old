from pathlib import Path
from typing import Any

from app.core.config import WORKSPACE_DIR
from app.runtime.python_content import is_valid_python
from app.tools.file_reader import read_file_content

MAX_PYTHON_CONTENT_CHARS = 50000
PROTECTED_DELETE_PATHS = {
    ".env",
    "project.txt",
}


def safe_path(relative_path: str) -> Path:
    target = (WORKSPACE_DIR / relative_path).resolve()

    try:
        target.relative_to(WORKSPACE_DIR)
    except ValueError:
        raise ValueError("Blocked: path is outside workspace")

    return target


def list_files() -> dict[str, Any]:
    files = []

    for path in WORKSPACE_DIR.rglob("*"):
        if path.is_file():
            files.append(str(path.relative_to(WORKSPACE_DIR)))

    return {
        "tool": "list_files",
        "workspace": str(WORKSPACE_DIR),
        "files": files,
    }


def read_file(path: str) -> dict[str, Any]:
    if not path:
        return {
            "tool": "read_file",
            "error": "Missing file path",
        }

    target = safe_path(path)

    if not target.exists():
        return {
            "tool": "read_file",
            "error": f"File not found: {path}",
        }

    if not target.is_file():
        return {
            "tool": "read_file",
            "error": f"Not a file: {path}",
        }

    parsed = read_file_content(target)

    if parsed.get("error"):
        return {
            "tool": "read_file",
            "path": path,
            "format": parsed.get("format"),
            "error": parsed["error"],
        }

    result = {
        "tool": "read_file",
        "path": path,
        "format": parsed.get("format"),
        "content": parsed.get("content", ""),
    }

    if parsed.get("truncated"):
        result["note"] = f"Content truncated to {len(result['content'])} characters."

    return result


def write_note(content: str) -> dict[str, Any]:
    if not content:
        return {
            "tool": "write_note",
            "error": "Missing note content",
        }

    from datetime import datetime

    notes_dir = WORKSPACE_DIR / "notes"
    notes_dir.mkdir(exist_ok=True)

    filename = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    target = notes_dir / filename

    target.write_text(content, encoding="utf-8")

    return {
        "tool": "write_note",
        "status": "success",
        "created_file": str(target.relative_to(WORKSPACE_DIR)),
    }


def create_file(path: str, content: str) -> dict[str, Any]:
    """Create a new file in workspace/notes folder (block if exists)."""
    if not path:
        return {
            "tool": "create_file",
            "error": "Missing file name",
        }

    if not content:
        return {
            "tool": "create_file",
            "error": "Missing file content",
        }

    # Always save to notes folder for user files
    notes_dir = WORKSPACE_DIR / "notes"
    notes_dir.mkdir(exist_ok=True)
    
    # Ensure path doesn't try to escape notes directory
    target = (notes_dir / path).resolve()
    
    try:
        target.relative_to(notes_dir)
    except ValueError:
        return {
            "tool": "create_file",
            "error": "Invalid file path",
        }

    if target.exists():
        return {
            "tool": "create_file",
            "error": f"File already exists: {path}",
        }

    # Create parent directories if needed
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return {
        "tool": "create_file",
        "status": "success",
        "created_file": str(target.relative_to(WORKSPACE_DIR)),
        "size_bytes": len(content),
    }


def _normalize_workspace_path(path: str) -> str:
    return path.replace("\\", "/").strip().lstrip("/")


def delete_file(path: str) -> dict[str, Any]:
    if not path:
        return {
            "tool": "delete_file",
            "error": "Missing file path",
        }

    normalized = _normalize_workspace_path(path)

    if normalized in PROTECTED_DELETE_PATHS:
        return {
            "tool": "delete_file",
            "error": f"Protected file cannot be deleted: {path}",
        }

    try:
        target = safe_path(normalized)
    except ValueError:
        return {
            "tool": "delete_file",
            "error": "Blocked: path is outside workspace",
        }

    if not target.exists():
        return {
            "tool": "delete_file",
            "error": f"File not found: {path}",
        }

    if not target.is_file():
        return {
            "tool": "delete_file",
            "error": f"Not a file: {path}",
        }

    target.unlink()

    return {
        "tool": "delete_file",
        "status": "success",
        "deleted_file": normalized,
    }


def write_python(path: str, content: str, run: bool = True) -> dict[str, Any]:
    if not path:
        return {
            "tool": "write_python",
            "error": "Missing file path",
        }

    if not content:
        return {
            "tool": "write_python",
            "error": "Missing Python code content",
        }

    if len(content) > MAX_PYTHON_CONTENT_CHARS:
        return {
            "tool": "write_python",
            "error": "Python file content exceeds 50 KB limit",
        }

    filename = Path(path).name
    if not filename.lower().endswith(".py"):
        filename = f"{Path(filename).stem or 'script'}.py"

    scripts_dir = WORKSPACE_DIR / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    target = (scripts_dir / filename).resolve()

    try:
        target.relative_to(scripts_dir.resolve())
    except ValueError:
        return {
            "tool": "write_python",
            "error": "Invalid Python file path",
        }

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    relative_path = str(target.relative_to(WORKSPACE_DIR)).replace("\\", "/")
    result: dict[str, Any] = {
        "tool": "write_python",
        "status": "success",
        "created_file": relative_path,
        "size_bytes": len(content),
        "source_preview": content[:2000],
    }

    if not is_valid_python(content):
        result["run_result"] = {
            "status": "error",
            "exit_code": 1,
            "stdout": "",
            "stderr": "Python syntax is invalid. Fix the code and try again.",
            "duration_ms": 0,
            "timed_out": False,
            "syntax_error": True,
        }
        return result

    if run:
        from app.tools.python_runner import run_python_file

        result["run_result"] = run_python_file(relative_path, source=content)

    return result


def execute_tool(action: str, args: dict[str, Any]) -> dict[str, Any]:
    if action == "list_files":
        return list_files()

    if action == "read_file":
        return read_file(args.get("path", ""))

    if action == "write_note":
        return write_note(args.get("content", ""))

    if action == "create_file":
        return create_file(
            args.get("path", ""),
            args.get("content", "")
        )

    if action == "delete_file":
        return delete_file(args.get("path", ""))

    if action == "write_python":
        return write_python(
            args.get("path", ""),
            args.get("content", ""),
            run=bool(args.get("run", True)),
        )

    return {
        "tool": action,
        "error": f"Unknown action: {action}",
    }
