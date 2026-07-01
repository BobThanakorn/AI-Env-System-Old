from pathlib import Path
from fastapi import HTTPException

from app.core.config import FRONTEND_DIR, WORKSPACE_DIR, AZURE_OPENAI_MODEL, ENV_PATH


def get_chat_page() -> str:
    chat_file = FRONTEND_DIR / "chat.html"

    if not chat_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"chat.html not found at {chat_file}",
        )

    html = chat_file.read_text(encoding="utf-8", errors="ignore")

    if not html.strip():
        raise HTTPException(
            status_code=500,
            detail="frontend/chat.html is empty",
        )

    return html


def get_health():
    return {
        "status": "ok",
        "service": "tcc-ai-environment-agent",
        "model": AZURE_OPENAI_MODEL,
    }


def get_env_debug():
    import os

    return {
        "env_file": str(ENV_PATH),
        "env_file_exists": ENV_PATH.exists(),
        "base_url_loaded": bool(os.getenv("AZURE_OPENAI_BASE_URL")),
        "api_key_loaded": bool(os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_API_KEY")),
        "model": AZURE_OPENAI_MODEL,
        "workspace_dir": str(WORKSPACE_DIR),
        "frontend_dir": str(FRONTEND_DIR),
        "frontend_dir_exists": FRONTEND_DIR.exists(),
        "chat_html_exists": (FRONTEND_DIR / "chat.html").exists(),
    }


def get_frontend_debug():
    chat_file = FRONTEND_DIR / "chat.html"
    css_file = FRONTEND_DIR / "style.css"
    js_file = FRONTEND_DIR / "app.js"

    return {
        "frontend_dir": str(FRONTEND_DIR),
        "frontend_dir_exists": FRONTEND_DIR.exists(),
        "chat_html_exists": chat_file.exists(),
        "chat_html_size": chat_file.stat().st_size if chat_file.exists() else 0,
        "style_css_exists": css_file.exists(),
        "style_css_size": css_file.stat().st_size if css_file.exists() else 0,
        "app_js_exists": js_file.exists(),
        "app_js_size": js_file.stat().st_size if js_file.exists() else 0,
        "chat_preview": (
            chat_file.read_text(encoding="utf-8", errors="ignore")[:300]
            if chat_file.exists()
            else None
        ),
    }
