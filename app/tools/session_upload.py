import re
import shutil
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import WORKSPACE_DIR

MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB
CHUNK_SIZE = 1024 * 1024
SESSION_ID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def validate_session_id(session_id: str) -> None:
    if not SESSION_ID_PATTERN.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id format")


def get_session_dir(session_id: str) -> Path:
    validate_session_id(session_id)
    return (WORKSPACE_DIR / "sessions" / session_id).resolve()


def get_upload_dir(session_id: str) -> Path:
    session_dir = get_session_dir(session_id)
    upload_dir = (session_dir / "upload").resolve()

    try:
        upload_dir.relative_to(WORKSPACE_DIR)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session path")

    return upload_dir


def _sanitize_filename(filename: str) -> str:
    name = Path(filename or "upload.bin").name.strip()
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return name


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_uploaded_file_info(session_id: str) -> dict | None:
    upload_dir = get_upload_dir(session_id)
    if not upload_dir.exists():
        return None

    files = [path for path in upload_dir.iterdir() if path.is_file()]
    if not files:
        return None

    target = files[0]
    size_bytes = target.stat().st_size

    return {
        "filename": target.name,
        "size_bytes": size_bytes,
        "size_label": _format_size(size_bytes),
        "path": str(target.relative_to(WORKSPACE_DIR)).replace("\\", "/"),
    }


def delete_session_uploads(session_id: str) -> None:
    session_dir = get_session_dir(session_id)
    if session_dir.exists():
        shutil.rmtree(session_dir, ignore_errors=True)


def clear_upload_dir(session_id: str) -> None:
    upload_dir = get_upload_dir(session_id)
    if upload_dir.exists():
        shutil.rmtree(upload_dir, ignore_errors=True)
    upload_dir.mkdir(parents=True, exist_ok=True)


async def save_session_upload(session_id: str, file: UploadFile) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    filename = _sanitize_filename(file.filename)
    clear_upload_dir(session_id)
    upload_dir = get_upload_dir(session_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    target = upload_dir / filename
    total_bytes = 0

    try:
        with target.open("wb") as output:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break

                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="File exceeds 100 MB limit",
                    )

                output.write(chunk)
    except HTTPException:
        if target.exists():
            target.unlink(missing_ok=True)
        raise
    except Exception as error:
        if target.exists():
            target.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {error}",
        ) from error
    finally:
        await file.close()

    if total_bytes == 0:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    return {
        "status": "success",
        "filename": filename,
        "size_bytes": total_bytes,
        "size_label": _format_size(total_bytes),
        "path": str(target.relative_to(WORKSPACE_DIR)).replace("\\", "/"),
    }
