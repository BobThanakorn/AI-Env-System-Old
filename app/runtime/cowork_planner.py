"""Planner for Cowork multi-step autonomous tasks."""

from __future__ import annotations

import json
from typing import Any

from app.core.azure_client import call_azure_ai
from app.core.token_usage import TokenUsage
from app.runtime.planner import (
    MAX_CONTEXT_MESSAGES,
    _build_messages,
    _track_call,
    answer_directly,
)
from app.runtime.parser import extract_json
from app.runtime.upload_context import build_upload_prompt_section

MAX_COWORK_STEPS = 8

COWORK_ACTIONS = """
Available actions:

1. done
Use when the user's goal is fully achieved based on completed steps.
Args: {"summary": "what was accomplished"}

2. answer
Use only when the goal is a simple question that needs no tools.

3. list_files — list workspace files
4. read_file — read a file. Args: {"path": "relative/path"}
5. write_note — save a note. Args: {"content": "..."}
6. create_file — create file in notes/. Args: {"path": "name.txt", "content": "..."}
7. delete_file — delete a file (requires user confirmation). Args: {"path": "..."}
8. write_python — create/run Python in scripts/. Args: {"path": "script.py", "content": "..."}

Rules:
- Work toward the user's GOAL step by step.
- Prefer read_file before summarizing or analyzing files.
- After creating/writing files, verify with read_file if helpful.
- Use "done" when deliverable is ready — do not repeat completed work.
- NEVER use "answer" to tell user to run commands manually.
"""


def _steps_context(steps: list[dict[str, Any]]) -> str:
    if not steps:
        return "No steps completed yet."
    return json.dumps(steps, ensure_ascii=False, indent=2)


def create_cowork_step(
    goal: str,
    steps: list[dict[str, Any]],
    context: list[dict[str, str]] | None = None,
    uploaded_file: dict[str, Any] | None = None,
    usage_tracker: TokenUsage | None = None,
) -> dict[str, Any]:
    system_prompt = (
        "You are a Cowork agent — an autonomous knowledge worker inside a local AI Environment.\n"
        "The user gave you a GOAL. You execute one action at a time until the goal is done.\n"
        + build_upload_prompt_section(uploaded_file)
        + COWORK_ACTIONS
        + "\n\nCompleted steps so far:\n"
        + _steps_context(steps)
        + "\n\nReturn only valid JSON (no markdown):\n"
        '{\n  "action": "...",\n  "args": {},\n  "reason": "why this step next"\n}'
    )

    content, usage = call_azure_ai(
        messages=_build_messages(system_prompt, f"GOAL: {goal}", context),
        max_tokens=1024,
    )
    _track_call(usage_tracker, usage)
    return extract_json(content)


def summarize_cowork_step(
    goal: str,
    plan: dict[str, Any],
    tool_result: dict[str, Any],
    usage_tracker: TokenUsage | None = None,
) -> str:
    prompt = (
        f"Goal: {goal}\n\n"
        f"Step plan:\n{json.dumps(plan, ensure_ascii=False)}\n\n"
        f"Tool result:\n{json.dumps(tool_result, ensure_ascii=False)}\n\n"
        "Write one short sentence (max 120 chars) describing what this step accomplished."
    )

    content, usage = call_azure_ai(
        messages=[
            {"role": "system", "content": "Summarize agent step briefly for a progress UI."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=256,
    )
    _track_call(usage_tracker, usage)
    return content.strip()


def finalize_cowork_task(
    goal: str,
    steps: list[dict[str, Any]],
    context: list[dict[str, str]] | None = None,
    uploaded_file: dict[str, Any] | None = None,
    usage_tracker: TokenUsage | None = None,
) -> str:
    if not steps:
        return answer_directly(
            goal,
            context=context,
            uploaded_file=uploaded_file,
            usage_tracker=usage_tracker,
        )

    system_prompt = (
        "You are a Cowork agent. The user assigned a goal and you completed multiple steps.\n"
        "Write a clear, helpful final deliverable for the user in Thai or English (match their language).\n"
        "Include what was done, key findings, and file paths created/modified.\n"
        "Be concise but complete — this is the finished outcome, not a chat reply."
        + build_upload_prompt_section(uploaded_file)
    )

    user_content = (
        f"GOAL:\n{goal}\n\n"
        f"COMPLETED STEPS:\n{json.dumps(steps, ensure_ascii=False, indent=2)}"
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if context:
        messages.extend(context[-MAX_CONTEXT_MESSAGES:])
    messages.append({"role": "user", "content": user_content})

    content, usage = call_azure_ai(messages=messages, max_tokens=2048)
    _track_call(usage_tracker, usage)
    return content
