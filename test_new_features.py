import io
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.memory.session_store import session_store
from app.runtime.confirmations import execute_pending_confirmation
from app.runtime.pending_actions import build_pending_action, is_confirmation_message
from app.tools.file_tools import delete_file, write_python
from main import app

client = TestClient(app)
session_id = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"

notes_dir_path = None


def setup_module():
    global notes_dir_path
    from app.core.config import WORKSPACE_DIR

    notes_dir_path = WORKSPACE_DIR / "notes" / "delete-me.txt"
    notes_dir_path.parent.mkdir(parents=True, exist_ok=True)
    notes_dir_path.write_text("temporary file", encoding="utf-8")


def teardown_module():
    if notes_dir_path and notes_dir_path.exists():
        notes_dir_path.unlink(missing_ok=True)

    from app.core.config import WORKSPACE_DIR

    script = WORKSPACE_DIR / "scripts" / "hello_test.py"
    if script.exists():
        script.unlink(missing_ok=True)


def test_write_python_runs_file():
    result = write_python(
        "hello_test.py",
        "print('py-run-ok')\nprint(2 + 2)",
        run=True,
    )

    assert result["status"] == "success"
    assert result["created_file"] == "scripts/hello_test.py"
    assert result["run_result"]["exit_code"] == 0
    assert "py-run-ok" in result["run_result"]["stdout"]
    assert "4" in result["run_result"]["stdout"]


def test_delete_file_requires_confirmation_flow():
    assert is_confirmation_message("ยืนยัน")
    assert is_confirmation_message("confirm")

    session_store.get_or_create(session_id)
    pending = build_pending_action("delete_file", {"path": "notes/delete-me.txt"})
    session_store.set_pending_action(session_id, pending)

    stored = session_store.get_pending_action(session_id)
    assert stored["confirmation_id"] == pending["confirmation_id"]

    cancel_result = execute_pending_confirmation(session_id, False)
    assert cancel_result["type"] == "confirmation_cancelled"
    assert session_store.get_pending_action(session_id) is None
    assert notes_dir_path.exists()

    session_store.set_pending_action(session_id, pending)
    confirm_result = execute_pending_confirmation(session_id, True)
    assert confirm_result["type"] == "confirmation_executed"
    assert confirm_result["tool_result"]["status"] == "success"
    assert not notes_dir_path.exists()


def test_agent_chat_delete_requests_confirmation():
    session_store.get_or_create(session_id)
    session_store.clear_pending_action(session_id)

    fake_plan = {
        "action": "delete_file",
        "args": {"path": "notes/will-not-delete.txt"},
        "reason": "test",
    }

    with patch("app.runtime.agent_runtime.create_plan", return_value=fake_plan):
        response = client.post(
            "/agent/chat",
            json={
                "message": "ลบไฟล์ notes/will-not-delete.txt",
                "session_id": session_id,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "confirmation_required"
    assert payload["pending_confirmation"] is not None
    assert payload["pending_confirmation"]["action"] == "delete_file"

    confirm_response = client.post(
        "/agent/confirm",
        json={
            "session_id": session_id,
            "confirmation_id": payload["pending_confirmation"]["confirmation_id"],
            "confirmed": False,
        },
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["type"] == "confirmation_cancelled"


def test_agent_chat_write_python_returns_run_canvas():
    session_store.get_or_create(session_id)

    fake_plan = {
        "action": "write_python",
        "args": {
            "path": "canvas_demo.py",
            "content": "print('canvas-demo')",
        },
        "reason": "test",
    }

    with patch("app.runtime.agent_runtime.create_plan", return_value=fake_plan):
        with patch(
            "app.runtime.agent_runtime.summarize_tool_result",
            return_value="Python script executed.",
        ):
            response = client.post(
                "/agent/chat",
                json={
                    "message": "เขียน python print canvas-demo",
                    "session_id": session_id,
                },
            )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_canvas"] is not None
    assert payload["run_canvas"]["file"] == "scripts/canvas_demo.py"
    assert "canvas-demo" in payload["run_canvas"]["stdout"]

    from app.core.config import WORKSPACE_DIR

    created = WORKSPACE_DIR / "scripts" / "canvas_demo.py"
    if created.exists():
        created.unlink()


if __name__ == "__main__":
    setup_module()
    try:
        test_write_python_runs_file()
        test_delete_file_requires_confirmation_flow()
        test_agent_chat_delete_requests_confirmation()
        test_agent_chat_write_python_returns_run_canvas()
        print("New feature tests passed.")
    finally:
        teardown_module()
