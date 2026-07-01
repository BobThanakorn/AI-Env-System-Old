from typing import Any

from app.core.token_usage import TokenUsage
from app.memory.session_store import session_store
from app.runtime.pending_actions import (
    build_delete_confirmation_message,
    build_pending_action,
    build_run_canvas,
)
from app.runtime.delete_context import (
    build_delete_fallback_plan,
    extract_delete_path,
    message_requests_delete,
    resolve_workspace_file_path,
)
from app.runtime.planner import answer_directly, create_plan, summarize_tool_result
from app.runtime.python_content import resolve_python_content
from app.runtime.upload_context import (
    build_upload_fallback_plan,
    message_refers_to_upload,
    normalize_tool_args,
)
from app.tools.file_tools import execute_tool


def run_agent(
    user_message: str,
    context: list[dict[str, str]] | None = None,
    uploaded_file: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    usage_tracker = TokenUsage()

    plan = create_plan(
        user_message,
        context=context,
        uploaded_file=uploaded_file,
        usage_tracker=usage_tracker,
    )

    action = plan.get("action", "answer")
    args = plan.get("args", {})

    if (
        action == "answer"
        and uploaded_file
        and message_refers_to_upload(user_message)
    ):
        plan = build_upload_fallback_plan(user_message, uploaded_file)
        action = plan["action"]
        args = plan["args"]

    if action == "answer" and message_requests_delete(user_message):
        delete_path = extract_delete_path(user_message)
        if delete_path:
            plan = build_delete_fallback_plan(delete_path)
            action = plan["action"]
            args = plan["args"]

    if action == "answer":
        return {
            "type": "direct_answer",
            "plan": plan,
            "tool_result": None,
            "answer": answer_directly(
                user_message,
                context=context,
                uploaded_file=uploaded_file,
                usage_tracker=usage_tracker,
            ),
            "usage": usage_tracker.to_dict(),
            "pending_confirmation": None,
            "run_canvas": None,
        }

    if action == "delete_file" and session_id:
        path = str(args.get("path", "")).strip()
        resolved = resolve_workspace_file_path(path)
        if resolved:
            path = resolved
        pending = build_pending_action("delete_file", {"path": path})
        session_store.set_pending_action(session_id, pending)

        return {
            "type": "confirmation_required",
            "plan": plan,
            "tool_result": None,
            "answer": build_delete_confirmation_message(path),
            "usage": usage_tracker.to_dict(),
            "pending_confirmation": pending,
            "run_canvas": None,
        }

    args = normalize_tool_args(action, args, uploaded_file)

    if action == "write_python":
        resolved_content, content_meta = resolve_python_content(
            str(args.get("content", "")),
            user_message,
        )
        args = {**args, "content": resolved_content}
        if content_meta.get("content_source") == "user_message_fallback":
            plan = {**plan, "content_resolution": content_meta}

    tool_result = execute_tool(action, args)
    final_answer = summarize_tool_result(
        user_message,
        plan,
        tool_result,
        context=context,
        uploaded_file=uploaded_file,
        usage_tracker=usage_tracker,
    )

    return {
        "type": "tool_using_agent",
        "plan": plan,
        "tool_result": tool_result,
        "answer": final_answer,
        "usage": usage_tracker.to_dict(),
        "pending_confirmation": None,
        "run_canvas": build_run_canvas(tool_result),
    }
