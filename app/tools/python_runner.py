import ast
import subprocess
import sys
import time
from pathlib import Path

from app.core.config import BASE_DIR, WORKSPACE_DIR
from app.tools.file_tools import safe_path

MAX_RUN_SECONDS = 15
MAX_OUTPUT_CHARS = 12000

WINDOWS_STATUS_MESSAGES = {
    0xC0000135: "Python failed to start (missing runtime DLL). Restart server using the project .venv.",
    0xC000013A: "Python process failed to initialize. Check that the project virtualenv is used.",
    0xC0000142: "Python DLL initialization failed.",
    0xC0000005: "Python crashed with an access violation.",
}


def get_python_executable() -> str:
    if sys.platform == "win32":
        venv_python = BASE_DIR / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)

    return sys.executable


def validate_python_source(content: str) -> str | None:
    try:
        ast.parse(content)
        return None
    except SyntaxError as error:
        return f"SyntaxError: {error.msg} (line {error.lineno})"


def describe_process_failure(exit_code: int, stderr: str) -> str:
    if stderr.strip():
        return stderr

    unsigned = exit_code & 0xFFFFFFFF
    if unsigned in WINDOWS_STATUS_MESSAGES:
        return WINDOWS_STATUS_MESSAGES[unsigned]

    if exit_code != 0:
        return f"Process exited with code {exit_code} and produced no output."

    return ""


def run_python_file(relative_path: str, source: str | None = None) -> dict:
    if not relative_path:
        return {"error": "Missing file path"}

    target = safe_path(relative_path)

    if not target.exists():
        return {"error": f"File not found: {relative_path}"}

    if not target.is_file():
        return {"error": f"Not a file: {relative_path}"}

    if target.suffix.lower() != ".py":
        return {"error": "Only .py files can be executed"}

    try:
        target.relative_to(WORKSPACE_DIR)
    except ValueError:
        return {"error": "Blocked: path is outside workspace"}

    code = source if source is not None else target.read_text(encoding="utf-8", errors="replace")
    syntax_error = validate_python_source(code)
    if syntax_error:
        return {
            "status": "error",
            "exit_code": 1,
            "stdout": "",
            "stderr": syntax_error,
            "duration_ms": 0,
            "timed_out": False,
            "syntax_error": True,
        }

    started = time.perf_counter()
    python_executable = get_python_executable()

    popen_kwargs: dict = {
        "cwd": str(WORKSPACE_DIR),
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "timeout": MAX_RUN_SECONDS,
    }

    if sys.platform == "win32":
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        completed = subprocess.run(
            [python_executable, "-u", str(target)],
            **popen_kwargs,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)

        stdout = (completed.stdout or "")[:MAX_OUTPUT_CHARS]
        stderr = describe_process_failure(completed.returncode, completed.stderr or "")
        stderr = stderr[:MAX_OUTPUT_CHARS]

        return {
            "status": "success" if completed.returncode == 0 else "error",
            "exit_code": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": duration_ms,
            "timed_out": False,
            "python_executable": python_executable,
        }
    except subprocess.TimeoutExpired as error:
        duration_ms = int((time.perf_counter() - started) * 1000)
        stdout = (error.stdout or "")[:MAX_OUTPUT_CHARS] if error.stdout else ""
        stderr = (error.stderr or "")[:MAX_OUTPUT_CHARS] if error.stderr else ""
        stderr = (stderr + f"\nExecution timed out after {MAX_RUN_SECONDS}s").strip()

        return {
            "status": "error",
            "exit_code": -1,
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": duration_ms,
            "timed_out": True,
            "python_executable": python_executable,
        }
    except Exception as error:
        return {
            "status": "error",
            "exit_code": -1,
            "stdout": "",
            "stderr": str(error),
            "duration_ms": 0,
            "timed_out": False,
            "python_executable": python_executable,
        }
