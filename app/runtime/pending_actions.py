import re
import uuid
from typing import Any

CONFIRM_PATTERN = re.compile(
    r"^(ยืนยัน|confirm|yes|ใช่|ตกลง|ok|okay|proceed|ลบเลย)\.?$",
    re.IGNORECASE,
)
CANCEL_PATTERN = re.compile(
    r"^(ยกเลิก|cancel|no|ไม่|ไม่ลบ|abort|stop)\.?$",
    re.IGNORECASE,
)


def is_confirmation_message(message: str) -> bool:
    return bool(CONFIRM_PATTERN.match(message.strip()))


def is_cancellation_message(message: str) -> bool:
    return bool(CANCEL_PATTERN.match(message.strip()))


def build_pending_action(action: str, args: dict[str, Any]) -> dict[str, Any]:
    return {
        "confirmation_id": str(uuid.uuid4()),
        "action": action,
        "args": args,
    }


def build_delete_confirmation_message(path: str) -> str:
    return (
        f"คุณต้องการลบไฟล์ `{path}` ใช่ไหม?\n"
        "กรุณากดปุ่ม ยืนยัน หรือพิมพ์ ยืนยัน เพื่อลบไฟล์\n"
        "หรือกดปุ่ม ยกเลิก / พิมพ์ ยกเลิก เพื่อยกเลิก"
    )


def build_run_canvas(tool_result: dict[str, Any]) -> dict[str, Any] | None:
    run_result = tool_result.get("run_result")
    if not run_result:
        return None

    return {
        "file": tool_result.get("created_file"),
        "exit_code": run_result.get("exit_code"),
        "stdout": run_result.get("stdout", ""),
        "stderr": run_result.get("stderr", ""),
        "duration_ms": run_result.get("duration_ms", 0),
        "timed_out": bool(run_result.get("timed_out")),
        "status": run_result.get("status", "error"),
        "source_preview": tool_result.get("source_preview", ""),
    }
