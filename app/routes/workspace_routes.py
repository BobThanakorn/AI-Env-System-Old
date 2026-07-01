from fastapi import APIRouter, HTTPException, Query

from app.core.config import WORKSPACE_DIR
from app.tools.file_reader import read_file_content
from app.tools.file_tools import list_files, safe_path

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("/files")
def workspace_files():
    result = list_files()
    files = []
    for relative in result.get("files", []):
        target = WORKSPACE_DIR / relative
        files.append(
            {
                "path": relative.replace("\\", "/"),
                "size_bytes": target.stat().st_size if target.is_file() else 0,
            }
        )
    files.sort(key=lambda item: item["path"])
    return {
        "workspace": str(WORKSPACE_DIR),
        "count": len(files),
        "files": files,
    }


@router.get("/file")
def workspace_file(path: str = Query(..., min_length=1)):
    normalized = path.replace("\\", "/").strip().lstrip("/")
    try:
        target = safe_path(normalized)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path is outside workspace")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    parsed = read_file_content(target)
    if parsed.get("error"):
        raise HTTPException(status_code=422, detail=parsed["error"])

    return {
        "path": normalized,
        "format": parsed.get("format"),
        "content": parsed.get("content", ""),
        "truncated": bool(parsed.get("truncated")),
    }
