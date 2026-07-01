"""Tests for Cowork multi-step runtime structure."""

from __future__ import annotations

import json
from unittest.mock import patch

from app.runtime.cowork_runtime import run_cowork_stream


def _mock_plan_responses():
    """First step reads file, second step marks done."""
    return [
        {
            "action": "list_files",
            "args": {},
            "reason": "See what files exist",
        },
        {
            "action": "done",
            "args": {"summary": "Listed workspace files"},
            "reason": "Goal achieved",
        },
    ]


@patch("app.runtime.cowork_runtime.summarize_cowork_step")
@patch("app.runtime.cowork_runtime.create_cowork_step")
@patch("app.runtime.cowork_runtime.finalize_cowork_task")
@patch("app.runtime.cowork_runtime.execute_tool")
def test_cowork_stream_events(mock_execute, mock_finalize, mock_step, mock_summarize):
    plans = _mock_plan_responses()
    mock_step.side_effect = plans
    mock_execute.return_value = {
        "tool": "list_files",
        "files": ["project.txt"],
        "workspace": "/workspace",
    }
    mock_summarize.return_value = "Listed files in workspace"
    mock_finalize.return_value = "Task complete: found project.txt"

    events = list(run_cowork_stream("List workspace files"))

    types = [event["type"] for event in events]
    assert types[0] == "task_started"
    assert "step_planned" in types
    assert "step_executed" in types
    assert types[-1] == "task_completed"
    assert events[-1]["answer"] == "Task complete: found project.txt"
    assert len(events[-1]["steps"]) == 1


@patch("app.runtime.cowork_runtime.answer_directly")
@patch("app.runtime.cowork_runtime.create_cowork_step")
def test_cowork_direct_answer(mock_step, mock_answer):
    mock_step.return_value = {
        "action": "answer",
        "args": {},
        "reason": "Simple question",
    }
    mock_answer.return_value = "Hello from cowork"

    events = list(run_cowork_stream("What can you do?"))
    completed = [event for event in events if event["type"] == "task_completed"]

    assert len(completed) == 1
    assert completed[0]["answer"] == "Hello from cowork"
    assert completed[0]["completed_via"] == "direct_answer"


def test_workspace_files_endpoint():
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    response = client.get("/workspace/files")
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert isinstance(data["files"], list)


if __name__ == "__main__":
    test_cowork_stream_events()
    test_cowork_direct_answer()
    test_workspace_files_endpoint()
    print("All cowork tests passed.")
