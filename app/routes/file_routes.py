from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.tools.file_tools import create_file

router = APIRouter(prefix="/files", tags=["files"])


class CreateFileRequest(BaseModel):
    filename: str
    content: str


@router.post("/create")
def create_file_endpoint(request: CreateFileRequest):
    """Create a new file directly (bypasses agent planning)."""
    
    filename = request.filename.strip()
    content = request.content.strip()

    if not filename:
        return {
            "status": "error",
            "message": "Filename cannot be empty",
        }

    if not content:
        return {
            "status": "error",
            "message": "Content cannot be empty",
        }

    # Call the tool directly
    result = create_file(filename, content)

    if "error" in result:
        return {
            "status": "error",
            "message": result["error"],
        }

    return {
        "status": "success",
        "message": f"ไฟล์ {filename} สร้างเรียบร้อยแล้ว",
        "file_path": result.get("created_file"),
        "size_bytes": result.get("size_bytes"),
    }
