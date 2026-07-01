import io

from fastapi.testclient import TestClient

from app.runtime.upload_context import (
    build_upload_fallback_plan,
    message_refers_to_upload,
    normalize_tool_args,
)
from app.tools.file_tools import read_file
from app.tools.session_upload import delete_session_uploads, get_uploaded_file_info
from main import app

client = TestClient(app)
session_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

file_content = b"Hello from uploaded chat file\nLine 2"
upload_response = client.post(
    f"/sessions/{session_id}/upload",
    files={"file": ("chat-upload.txt", io.BytesIO(file_content), "text/plain")},
)
assert upload_response.status_code == 200, upload_response.text

uploaded_file = get_uploaded_file_info(session_id)
assert uploaded_file is not None
assert uploaded_file["filename"] == "chat-upload.txt"
assert "sessions/" in uploaded_file["path"]

read_result = read_file(uploaded_file["path"])
assert read_result.get("error") is None
assert "Hello from uploaded chat file" in read_result["content"]

assert message_refers_to_upload("สรุปไฟล์ที่แนบให้หน่อย")
assert message_refers_to_upload("What is in this uploaded file?")
assert not message_refers_to_upload("Hello there")

normalized = normalize_tool_args(
    "read_file",
    {"path": "chat-upload.txt"},
    uploaded_file,
)
assert normalized["path"] == uploaded_file["path"]

fallback_plan = build_upload_fallback_plan("สรุปไฟล์นี้", uploaded_file)
assert fallback_plan["action"] == "read_file"
assert fallback_plan["args"]["path"] == uploaded_file["path"]

delete_session_uploads(session_id)
assert get_uploaded_file_info(session_id) is None

print("Upload chat integration tests passed.")
