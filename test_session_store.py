from app.memory.session_store import session_store

session_id = "unit-test-session"

session_store.add_message(session_id, "user", "hello")
session_store.add_message(session_id, "assistant", "hi there")

context = session_store.get_context(session_id)
assert len(context) == 2
assert context[0]["content"] == "hello"
assert context[1]["content"] == "hi there"

assert session_store.delete_session(session_id) is True
assert session_store.get_context(session_id) == []
assert session_store.delete_session(session_id) is False

print("Session store unit tests passed.")
