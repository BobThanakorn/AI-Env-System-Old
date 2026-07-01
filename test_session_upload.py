import io

from fastapi.testclient import TestClient

from app.tools.session_upload import (
    MAX_UPLOAD_BYTES,
    clear_upload_dir,
    delete_session_uploads,
    get_uploaded_file_info,
    validate_session_id,
)
from main import app

client = TestClient(app)
session_id = "11111111-2222-3333-4444-555555555555"

try:
    validate_session_id("bad-id")
    raise AssertionError("Expected invalid session_id to fail")
except Exception:
    pass

validate_session_id(session_id)

small_content = b"hello session upload"
response = client.post(
    f"/sessions/{session_id}/upload",
    files={"file": ("test.txt", io.BytesIO(small_content), "text/plain")},
)
assert response.status_code == 200, response.text
payload = response.json()
assert payload["file"]["filename"] == "test.txt"
assert payload["file"]["size_bytes"] == len(small_content)

info = get_uploaded_file_info(session_id)
assert info is not None
assert info["filename"] == "test.txt"

get_response = client.get(f"/sessions/{session_id}/upload")
assert get_response.status_code == 200
assert get_response.json()["file"]["filename"] == "test.txt"

replace_content = b"replacement file"
replace_response = client.post(
    f"/sessions/{session_id}/upload",
    files={"file": ("new.txt", io.BytesIO(replace_content), "text/plain")},
)
assert replace_response.status_code == 200
assert replace_response.json()["file"]["filename"] == "new.txt"

info_after_replace = get_uploaded_file_info(session_id)
assert info_after_replace["filename"] == "new.txt"
assert get_uploaded_file_info(session_id)["filename"] == "new.txt"

too_large = b"x" * (MAX_UPLOAD_BYTES + 1)
large_response = client.post(
    f"/sessions/{session_id}/upload",
    files={"file": ("large.bin", io.BytesIO(too_large), "application/octet-stream")},
)
assert large_response.status_code == 413

delete_upload_response = client.delete(f"/sessions/{session_id}/upload")
assert delete_upload_response.status_code == 200
assert get_uploaded_file_info(session_id) is None

delete_session_response = client.delete(f"/sessions/{session_id}")
assert delete_session_response.status_code == 200

print("Session upload tests passed.")
