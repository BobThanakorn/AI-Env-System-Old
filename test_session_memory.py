from fastapi.testclient import TestClient
from main import app
from app.memory.session_store import session_store

client = TestClient(app)

session_id = "test-session-123"

r1 = client.post(
    "/agent/chat",
    json={"message": "My name is TestUser", "session_id": session_id},
)
assert r1.status_code == 200
assert r1.json()["session_id"] == session_id

context = session_store.get_context(session_id)
assert len(context) == 2
assert context[0]["role"] == "user"
assert "TestUser" in context[0]["content"]

r2 = client.post(
    "/agent/chat",
    json={"message": "What is my name?", "session_id": session_id},
)
assert r2.status_code == 200

context_after = session_store.get_context(session_id)
assert len(context_after) == 4

deleted = client.delete(f"/sessions/{session_id}")
assert deleted.status_code == 200
assert deleted.json()["deleted"] is True
assert session_id not in session_store.sessions

print("Session memory tests passed.")
