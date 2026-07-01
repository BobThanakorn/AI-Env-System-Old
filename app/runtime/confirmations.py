from typing import Any

from app.memory.session_store import session_store
from app.runtime.pending_actions import build_run_canvas
from app.runtime.planner import summarize_tool_result
from app.tools.file_tools import execute_tool


def execute_pending_confirmation(session_id: str, confirmed: bool) -> dict[str, Any]:
    pending = session_store.get_pending_action(session_id)
    if not pending:
        return {
            "type": "confirmation_error",
            "answer": "ไม่พบคำขอที่รอยืนยัน",
            "pending_confirmation": None,
            "run_canvas": None,
        }

    session_store.clear_pending_action(session_id)

    if not confirmed:
        action = pending.get("action", "action")
        path = pending.get("args", {}).get("path", "")
        return {
            "type": "confirmation_cancelled",
            "answer": f"ยกเลิกการ{action} `{path}` แล้ว",
            "pending_confirmation": None,
            "run_canvas": None,
            "tool_result": None,
            "plan": pending,
        }

    action = pending.get("action", "")
    args = pending.get("args", {})
    tool_result = execute_tool(action, args)

    if tool_result.get("status") == "success":
        deleted_file = tool_result.get("deleted_file", args.get("path", ""))
        answer = f"ลบไฟล์ `{deleted_file}` เรียบร้อยแล้ว"
    else:
        answer = tool_result.get("error") or "ไม่สามารถดำเนินการได้"

    return {
        "type": "confirmation_executed",
        "answer": answer,
        "pending_confirmation": None,
        "run_canvas": build_run_canvas(tool_result),
        "tool_result": tool_result,
        "plan": pending,
    }


def build_agent_response(
    result: dict[str, Any],
    session_id: str,
    usage: dict | None = None,
) -> dict[str, Any]:
    request_usage = usage if usage is not None else result.get("usage", {})

    return {
        **result,
        "session_id": session_id,
        "usage": {
            "request": request_usage,
            "session": session_store.get_token_usage(session_id),
        },
        "uploaded_file": session_store.get_uploaded_file(session_id),
        "pending_confirmation": result.get("pending_confirmation"),
        "run_canvas": result.get("run_canvas"),
        "steps": result.get("steps", []),
    }
