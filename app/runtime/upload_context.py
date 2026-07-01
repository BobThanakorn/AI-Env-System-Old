import re
from typing import Any

UPLOAD_INTENT_PATTERN = re.compile(
    r"(ไฟล์ที่แนบ|ไฟล์ที่อัพ|ไฟล์ที่อัป|อัพโหลด|อัปโหลด|แนบมา|ไฟล์นี้|ไฟล์ที่ส่ง|"
    r"uploaded\s+file|attached\s+file|this\s+file|the\s+upload|my\s+upload|"
    r"read\s+uploaded|summarize\s+upload|analyze\s+upload|"
    r"สรุปไฟล์|อ่านไฟล์ที่|อ่านไฟล์ที่แนบ|สรุปไฟล์ที่แนบ|"
    r"analyze\s+(this|the|my)\s+file|summarize\s+(this|the|my)\s+file)",
    re.IGNORECASE,
)


def build_upload_prompt_section(uploaded_file: dict[str, Any] | None) -> str:
    if not uploaded_file:
        return (
            "\nSESSION UPLOAD:\n"
            "No file is attached to this chat session.\n"
        )

    filename = uploaded_file.get("filename", "unknown")
    path = uploaded_file.get("path", "")
    size_label = uploaded_file.get("size_label", "")

    return (
        "\nSESSION UPLOAD:\n"
        f"The user attached 1 file to this chat session.\n"
        f"- filename: {filename}\n"
        f"- workspace path: {path}\n"
        f"- size: {size_label}\n"
        "Supported reading: .pdf (text-based), .txt, .md, .csv, .json\n"
        "When the user asks about the attached/uploaded file, or says things like "
        '"read uploaded file", "สรุปไฟล์ที่แนบ", or "what is in this file", '
        f'use read_file with path "{path}".\n'
        "Do not guess a different path.\n"
    )


def message_refers_to_upload(message: str) -> bool:
    return bool(UPLOAD_INTENT_PATTERN.search(message))


def normalize_tool_args(
    action: str,
    args: dict[str, Any],
    uploaded_file: dict[str, Any] | None,
) -> dict[str, Any]:
    if action != "read_file" or not uploaded_file:
        return args

    path = str(args.get("path", "")).strip()
    upload_path = uploaded_file.get("path", "")
    filename = uploaded_file.get("filename", "")

    if not path or path == filename or path.endswith("/" + filename):
        return {**args, "path": upload_path}

    return args


def build_upload_fallback_plan(
    user_message: str,
    uploaded_file: dict[str, Any],
) -> dict[str, Any]:
    return {
        "action": "read_file",
        "args": {"path": uploaded_file["path"]},
        "reason": "User asked about the session upload",
    }
