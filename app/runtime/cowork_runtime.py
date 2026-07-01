"""Cowork multi-step autonomous agent runtime with streaming events."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from app.core.token_usage import TokenUsage
from app.memory.session_store import session_store
from app.runtime.cowork_planner import (
    MAX_COWORK_STEPS,
    create_cowork_step,
    finalize_cowork_task,
    summarize_cowork_step,
)
from app.runtime.delete_context import (
    build_delete_fallback_plan,
    extract_delete_path,
    message_requests_delete,
    resolve_workspace_file_path,
)
from app.runtime.pending_actions import (
    build_delete_confirmation_message,
    build_pending_action,
    build_run_canvas,
)
from app.runtime.planner import answer_directly
from app.runtime.python_content import resolve_python_content
from app.runtime.upload_context import (
    build_upload_fallback_plan,
    message_refers_to_upload,
    normalize_tool_args,
)
from app.tools.file_tools import execute_tool


def _event(event_type: str, **payload: Any) -> dict[str, Any]:
    return {"type": event_type, **payload}


def run_cowork_stream(
    goal: str,
    context: list[dict[str, str]] | None = None,
    uploaded_file: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> Iterator[dict[str, Any]]:
    usage_tracker = TokenUsage()
    steps: list[dict[str, Any]] = []
    last_run_canvas: dict[str, Any] | None = None

    yield _event("task_started", goal=goal, max_steps=MAX_COWORK_STEPS)

    for step_num in range(1, MAX_COWORK_STEPS + 1):
        plan = create_cowork_step(
            goal,
            steps,
            context=context,
            uploaded_file=uploaded_file,
            usage_tracker=usage_tracker,
        )

        action = plan.get("action", "answer")
        args = plan.get("args", {})

        if (
            action == "answer"
            and not steps
            and uploaded_file
            and message_refers_to_upload(goal)
        ):
            plan = build_upload_fallback_plan(goal, uploaded_file)
            action = plan["action"]
            args = plan["args"]

        if action == "answer" and not steps and message_requests_delete(goal):
            delete_path = extract_delete_path(goal)
            if delete_path:
                plan = build_delete_fallback_plan(delete_path)
                action = plan["action"]
                args = plan["args"]

        yield _event("step_planned", step=step_num, plan=plan)

        if action == "done":
            break

        if action == "answer" and not steps:
            answer = answer_directly(
                goal,
                context=context,
                uploaded_file=uploaded_file,
                usage_tracker=usage_tracker,
            )
            yield _event(
                "task_completed",
                answer=answer,
                steps=steps,
                usage=usage_tracker.to_dict(),
                run_canvas=None,
                pending_confirmation=None,
                completed_via="direct_answer",
            )
            return

        if action == "delete_file" and session_id:
            path = str(args.get("path", "")).strip()
            resolved = resolve_workspace_file_path(path)
            if resolved:
                path = resolved
            pending = build_pending_action("delete_file", {"path": path})
            session_store.set_pending_action(session_id, pending)

            yield _event(
                "confirmation_required",
                step=step_num,
                plan=plan,
                answer=build_delete_confirmation_message(path),
                pending_confirmation=pending,
                steps=steps,
                usage=usage_tracker.to_dict(),
            )
            return

        args = normalize_tool_args(action, args, uploaded_file)

        if action == "write_python":
            resolved_content, content_meta = resolve_python_content(
                str(args.get("content", "")),
                goal,
            )
            args = {**args, "content": resolved_content}
            if content_meta.get("content_source") == "user_message_fallback":
                plan = {**plan, "content_resolution": content_meta}

        tool_result = execute_tool(action, args)
        canvas = build_run_canvas(tool_result)
        if canvas:
            last_run_canvas = canvas

        step_summary = summarize_cowork_step(goal, plan, tool_result, usage_tracker)

        step_record = {
            "step": step_num,
            "plan": plan,
            "tool_result": tool_result,
            "summary": step_summary,
        }
        steps.append(step_record)

        yield _event(
            "step_executed",
            step=step_num,
            plan=plan,
            tool_result=tool_result,
            summary=step_summary,
            run_canvas=canvas,
        )

        if tool_result.get("error"):
            yield _event(
                "step_error",
                step=step_num,
                error=tool_result["error"],
            )

    final_answer = finalize_cowork_task(
        goal,
        steps,
        context=context,
        uploaded_file=uploaded_file,
        usage_tracker=usage_tracker,
    )

    yield _event(
        "task_completed",
        answer=final_answer,
        steps=steps,
        usage=usage_tracker.to_dict(),
        run_canvas=last_run_canvas,
        pending_confirmation=None,
        completed_via="cowork_loop",
    )


def run_cowork(
    goal: str,
    context: list[dict[str, str]] | None = None,
    uploaded_file: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Run cowork and collect the final result (non-streaming)."""
    result: dict[str, Any] | None = None

    for event in run_cowork_stream(goal, context, uploaded_file, session_id):
        if event["type"] in ("task_completed", "confirmation_required"):
            result = event

    if result is None:
        return {
            "type": "cowork_error",
            "answer": "Cowork task ended without a result.",
            "steps": [],
            "usage": {},
        }

    if result["type"] == "confirmation_required":
        return {
            "type": "confirmation_required",
            "plan": result.get("plan"),
            "tool_result": None,
            "answer": result["answer"],
            "usage": result.get("usage", {}),
            "pending_confirmation": result.get("pending_confirmation"),
            "run_canvas": None,
            "steps": result.get("steps", []),
        }

    return {
        "type": "cowork_completed",
        "plan": {"action": "cowork", "reason": goal},
        "tool_result": {"steps": result.get("steps", [])},
        "answer": result["answer"],
        "usage": result.get("usage", {}),
        "pending_confirmation": None,
        "run_canvas": result.get("run_canvas"),
        "steps": result.get("steps", []),
    }


def cowork_events_to_sse(events: Iterator[dict[str, Any]]) -> Iterator[str]:
    for event in events:
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"
