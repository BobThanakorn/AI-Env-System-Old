from uuid import uuid4

import json

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.memory.session_store import session_store
from app.runtime.agent_runtime import run_agent
from app.runtime.confirmations import build_agent_response, execute_pending_confirmation
from app.runtime.cowork_runtime import run_cowork, run_cowork_stream
from app.runtime.pending_actions import is_cancellation_message, is_confirmation_message
from app.tools.session_upload import (
    clear_upload_dir,
    get_uploaded_file_info,
    save_session_upload,
    validate_session_id,
)

router = APIRouter()


class AgentRequest(BaseModel):
    message: str
    session_id: str | None = None
    mode: str = "chat"


class CoworkRequest(BaseModel):
    goal: str
    session_id: str | None = None


class ConfirmRequest(BaseModel):
    session_id: str
    confirmation_id: str
    confirmed: bool


class SessionDeleteRequest(BaseModel):
    session_id: str


@router.post("/agent/chat")
def agent_chat(request: AgentRequest):
    session_id = request.session_id or str(uuid4())
    session_store.get_or_create(session_id)

    context = session_store.get_context(session_id)
    session_store.add_message(session_id, "user", request.message)

    pending = session_store.get_pending_action(session_id)
    if pending:
        if is_confirmation_message(request.message):
            result = execute_pending_confirmation(session_id, True)
            session_store.add_message(session_id, "assistant", result["answer"])
            return build_agent_response(result, session_id)

        if is_cancellation_message(request.message):
            result = execute_pending_confirmation(session_id, False)
            session_store.add_message(session_id, "assistant", result["answer"])
            return build_agent_response(result, session_id)

    uploaded_file = session_store.get_uploaded_file(session_id)

    if request.mode == "cowork":
        result = _run_cowork_request(session_id, request.message, context, uploaded_file)
        session_store.add_message(session_id, "assistant", result["answer"])
        request_usage = result.get("usage", {})
        session_store.add_token_usage(session_id, request_usage)
        return build_agent_response(result, session_id, usage=request_usage)

    result = run_agent(
        request.message,
        context=context,
        uploaded_file=uploaded_file,
        session_id=session_id,
    )
    session_store.add_message(session_id, "assistant", result["answer"])

    request_usage = result.get("usage", {})
    session_store.add_token_usage(session_id, request_usage)

    return build_agent_response(result, session_id, usage=request_usage)


def _run_cowork_request(
    session_id: str,
    goal: str,
    context: list[dict[str, str]],
    uploaded_file: dict | None,
) -> dict:
    return run_cowork(goal, context=context, uploaded_file=uploaded_file, session_id=session_id)


@router.post("/agent/cowork")
def agent_cowork(request: CoworkRequest):
    session_id = request.session_id or str(uuid4())
    session_store.get_or_create(session_id)
    session_store.add_message(session_id, "user", request.goal)

    context = session_store.get_context(session_id)
    uploaded_file = session_store.get_uploaded_file(session_id)

    def event_generator():
        final_usage: dict = {}
        final_answer = ""

        for event in run_cowork_stream(
            request.goal,
            context=context,
            uploaded_file=uploaded_file,
            session_id=session_id,
        ):
            if event.get("usage"):
                final_usage = event["usage"]
            if event["type"] == "task_completed":
                final_answer = event.get("answer", "")
            elif event["type"] == "confirmation_required":
                final_answer = event.get("answer", "")

            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

        if final_answer:
            session_store.add_message(session_id, "assistant", final_answer)
        if final_usage:
            session_store.add_token_usage(session_id, final_usage)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str):
    validate_session_id(session_id)
    conversation = session_store.get_or_create(session_id)
    return {
        "session_id": session_id,
        "messages": [message.to_dict() for message in conversation.messages],
        "usage": session_store.get_token_usage(session_id),
        "uploaded_file": session_store.get_uploaded_file(session_id),
    }


@router.post("/agent/confirm")
def confirm_agent_action(request: ConfirmRequest):
    validate_session_id(request.session_id)
    session_store.get_or_create(request.session_id)

    pending = session_store.get_pending_action(request.session_id)
    if not pending:
        return {
            "session_id": request.session_id,
            "type": "confirmation_error",
            "answer": "ไม่พบคำขอที่รอยืนยัน",
            "pending_confirmation": None,
            "run_canvas": None,
        }

    if pending.get("confirmation_id") != request.confirmation_id:
        return {
            "session_id": request.session_id,
            "type": "confirmation_error",
            "answer": "รหัสยืนยันไม่ถูกต้อง กรุณาลองใหม่",
            "pending_confirmation": pending,
            "run_canvas": None,
        }

    role = "user" if request.confirmed else "system"
    label = "ยืนยัน" if request.confirmed else "ยกเลิก"
    session_store.add_message(request.session_id, role, label)

    result = execute_pending_confirmation(request.session_id, request.confirmed)
    session_store.add_message(request.session_id, "assistant", result["answer"])

    return build_agent_response(result, request.session_id)


@router.post("/sessions/{session_id}/upload")
async def upload_session_file(session_id: str, file: UploadFile = File(...)):
    validate_session_id(session_id)
    session_store.get_or_create(session_id)

    result = await save_session_upload(session_id, file)
    session_store.set_uploaded_file(session_id, result)

    return {
        "session_id": session_id,
        "file": result,
    }


@router.get("/sessions/{session_id}/upload")
def get_session_upload(session_id: str):
    validate_session_id(session_id)
    file_info = session_store.get_uploaded_file(session_id)

    return {
        "session_id": session_id,
        "file": file_info,
    }


@router.delete("/sessions/{session_id}/upload")
def delete_session_upload(session_id: str):
    validate_session_id(session_id)
    clear_upload_dir(session_id)
    session_store.set_uploaded_file(session_id, None)

    return {
        "session_id": session_id,
        "deleted": True,
    }


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    validate_session_id(session_id)
    deleted = session_store.delete_session(session_id)
    return {
        "session_id": session_id,
        "deleted": deleted,
    }


@router.post("/sessions/clear")
def clear_session(request: SessionDeleteRequest):
    validate_session_id(request.session_id)
    deleted = session_store.delete_session(request.session_id)
    return {
        "session_id": request.session_id,
        "deleted": deleted,
    }


@router.get("/sessions/{session_id}/usage")
def get_session_usage(session_id: str):
    validate_session_id(session_id)
    return {
        "session_id": session_id,
        "usage": session_store.get_token_usage(session_id),
    }
