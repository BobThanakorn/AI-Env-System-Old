from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.routes.utils import get_chat_page, get_health, get_env_debug, get_frontend_debug

router = APIRouter()


@router.get("/")
def root():
    return {
        "message": "TCC AI Environment Agent is running",
        "chat_url": "/chat",
        "create_file_url": "/create-file",
        "health_url": "/health",
        "docs_url": "/docs",
    }


@router.get("/chat", response_class=HTMLResponse)
def chat_page():
    html = get_chat_page()
    return HTMLResponse(content=html)


@router.get("/create-file", response_class=HTMLResponse)
def create_file_page():
    """Serve the create file page."""
    from app.core.config import FRONTEND_DIR
    
    create_file_file = FRONTEND_DIR / "create_file.html"

    if not create_file_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"create_file.html not found at {create_file_file}",
        )

    html = create_file_file.read_text(encoding="utf-8", errors="ignore")

    if not html.strip():
        raise HTTPException(
            status_code=500,
            detail="frontend/create_file.html is empty",
        )

    return HTMLResponse(content=html)


@router.get("/health")
def health():
    return get_health()


@router.get("/debug/env")
def debug_env():
    return get_env_debug()


@router.get("/debug/frontend")
def debug_frontend():
    return get_frontend_debug()
