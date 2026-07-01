from pathlib import Path

from app.core.config import WORKSPACE_DIR
from app.runtime.delete_context import (
    build_delete_fallback_plan,
    extract_delete_path,
    message_requests_delete,
    resolve_workspace_file_path,
)

scripts_dir = WORKSPACE_DIR / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)
hello_path = scripts_dir / "Hello.py"
hello_path.write_text("print('x')\n", encoding="utf-8")

assert message_requests_delete("ลบไฟล์ Hello.py")
assert extract_delete_path("ลบไฟล์ Hello.py") == "Hello.py"
assert resolve_workspace_file_path("Hello.py") == "scripts/Hello.py"

plan = build_delete_fallback_plan("Hello.py")
assert plan["action"] == "delete_file"
assert plan["args"]["path"] == "scripts/Hello.py"

from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
session_id = "dddddddd-eeee-ffff-0000-111111111111"

fake_plan = {"action": "answer", "args": {}, "reason": "wrong"}

with patch("app.runtime.agent_runtime.create_plan", return_value=fake_plan):
    response = client.post(
        "/agent/chat",
        json={"message": "ลบไฟล์ Hello.py", "session_id": session_id},
    )

assert response.status_code == 200
payload = response.json()
assert payload["type"] == "confirmation_required", payload
assert payload["pending_confirmation"]["action"] == "delete_file"
assert payload["pending_confirmation"]["args"]["path"] == "scripts/Hello.py"

if hello_path.exists():
    hello_path.unlink()

print("Delete fallback tests passed.")
