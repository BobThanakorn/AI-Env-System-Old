import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent.parent.resolve()
ENV_PATH = BASE_DIR / ".env"
WORKSPACE_DIR = (BASE_DIR / "workspace").resolve()
FRONTEND_DIR = (BASE_DIR / "frontend").resolve()
AUDIT_LOG_DIR = (WORKSPACE_DIR / "audit_logs").resolve()
SESSIONS_DIR = (WORKSPACE_DIR / "sessions").resolve()

load_dotenv(ENV_PATH, override=True)

WORKSPACE_DIR.mkdir(exist_ok=True)
FRONTEND_DIR.mkdir(exist_ok=True)
AUDIT_LOG_DIR.mkdir(exist_ok=True)
SESSIONS_DIR.mkdir(exist_ok=True)

AZURE_OPENAI_BASE_URL = os.getenv("AZURE_OPENAI_BASE_URL")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_API_KEY")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL", "gpt-5.1-codex-mini")

if not AZURE_OPENAI_BASE_URL:
    raise ValueError("Missing AZURE_OPENAI_BASE_URL in .env")

if not AZURE_OPENAI_API_KEY:
    raise ValueError("Missing AZURE_OPENAI_API_KEY in .env")
