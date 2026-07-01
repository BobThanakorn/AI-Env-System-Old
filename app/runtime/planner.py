import json
from typing import Any

from app.core.azure_client import call_azure_ai
from app.core.token_usage import TokenUsage
from app.runtime.parser import extract_json
from app.runtime.upload_context import build_upload_prompt_section

MAX_CONTEXT_MESSAGES = 20


def _build_messages(
    system_prompt: str,
    user_message: str,
    context: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    if context:
        messages.extend(context[-MAX_CONTEXT_MESSAGES:])

    messages.append({"role": "user", "content": user_message})
    return messages


def _track_call(usage_tracker: TokenUsage | None, usage: dict[str, int]) -> None:
    if usage_tracker is not None:
        usage_tracker.add_from_dict(usage)


def create_plan(
    user_message: str,
    context: list[dict[str, str]] | None = None,
    uploaded_file: dict[str, Any] | None = None,
    usage_tracker: TokenUsage | None = None,
) -> dict[str, Any]:
    system_prompt = """
You are an AI agent running inside a local AI Environment.

You must choose exactly one action.
Use conversation history when the user refers to previous messages.
""" + build_upload_prompt_section(uploaded_file) + """
Available actions:

1. answer
Use this when no tool is needed.

2. list_files
Use this when the user asks what files exist in the workspace.

3. read_file
Use this when the user asks to read, inspect, or summarize a file.
Supports text files and PDF (.pdf). If the user asks about the attached session upload, use the upload path from SESSION UPLOAD.
Args example:
{"path": "project.txt"}

4. write_note
Use this when the user asks to save or write a note.
Args example:
{"content": "markdown note content"}

5. create_file
Use this when the user asks to create a new file with specific content.
Keywords: สร้างไฟล์, create file, new file
Args example:
{"path": "myfile.txt", "content": "file content here"}

6. delete_file
Use this when the user asks to delete or remove a file in the workspace.
Keywords: ลบ, ลบไฟล์, delete file, remove file
Args example:
{"path": "scripts/hello.py"}
IMPORTANT:
- If user says "ลบไฟล์ Hello.py" and the file was created by write_python, use path "scripts/Hello.py"
- If user gives only a filename, prefer scripts/ or notes/ when that is where the file lives
- Deletion always requires user confirmation before it runs
- NEVER use action "answer" to tell the user to use rm/del manually

7. write_python
Use this when the user asks to create/write/run a Python (.py) script.
Keywords: เขียน python, สร้างไฟล์ .py, run python, python script
Args example:
{"path": "hello.py", "content": "print('hello')"}
IMPORTANT: In JSON, use single quotes inside Python code when possible.
Example for Hello World: {"path": "Hello.py", "content": "print('Hello World')"}
Files are saved under workspace/scripts/ and executed automatically.

IMPORTANT for create_file:
- If user says "สร้างไฟล์ชื่อ X ด้วยเนื้อหา Y" → action="create_file", path="X", content="Y"
- If user says "create file X with content Y" → action="create_file"
- Extract path and content carefully from the message

Return only valid JSON.
Do not use markdown.
Do not explain outside JSON.

Format:
{
  "action": "answer | list_files | read_file | write_note | create_file | delete_file | write_python",
  "args": {},
  "reason": "short reason"
}
"""

    content, usage = call_azure_ai(
        messages=_build_messages(system_prompt, user_message, context),
        max_tokens=1024,
    )
    _track_call(usage_tracker, usage)

    return extract_json(content)


def answer_directly(
    user_message: str,
    context: list[dict[str, str]] | None = None,
    uploaded_file: dict[str, Any] | None = None,
    usage_tracker: TokenUsage | None = None,
) -> str:
    system_prompt = (
        "You are a helpful AI agent inside a local AI Environment. "
        "You can use tools for files in the workspace through the planner. "
        "Never tell the user you cannot delete files — deletion is handled by delete_file with confirmation. "
        "Use conversation history to answer follow-up questions naturally."
        + build_upload_prompt_section(uploaded_file)
    )

    content, usage = call_azure_ai(
        messages=_build_messages(system_prompt, user_message, context),
        max_tokens=2048,
    )
    _track_call(usage_tracker, usage)

    return content


def summarize_tool_result(
    user_message: str,
    plan: dict[str, Any],
    tool_result: dict[str, Any],
    context: list[dict[str, str]] | None = None,
    uploaded_file: dict[str, Any] | None = None,
    usage_tracker: TokenUsage | None = None,
) -> str:
    tool_context = (
        "Agent plan:\n"
        + json.dumps(plan, ensure_ascii=False, indent=2)
        + "\n\nTool result:\n"
        + json.dumps(tool_result, ensure_ascii=False, indent=2)
    )

    system_prompt = (
        "You are an AI agent. Summarize the tool result clearly for the user. "
        "Use conversation history when relevant."
        + build_upload_prompt_section(uploaded_file)
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    if context:
        messages.extend(context[-MAX_CONTEXT_MESSAGES:])

    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "user", "content": tool_context})

    content, usage = call_azure_ai(messages=messages, max_tokens=2048)
    _track_call(usage_tracker, usage)

    return content
