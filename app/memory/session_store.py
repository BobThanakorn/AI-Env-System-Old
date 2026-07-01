from app.memory.conversation import Conversation
from app.tools.session_upload import delete_session_uploads, get_uploaded_file_info


class SessionStore:
    def __init__(self) -> None:
        self.sessions: dict[str, Conversation] = {}

    def get_or_create(self, session_id: str) -> Conversation:
        if session_id not in self.sessions:
            self.sessions[session_id] = Conversation(session_id)
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str) -> None:
        conversation = self.get_or_create(session_id)
        conversation.add_message(role, content)

    def add_token_usage(self, session_id: str, usage: dict) -> None:
        conversation = self.get_or_create(session_id)
        conversation.token_usage.add_from_dict(usage)

    def set_uploaded_file(self, session_id: str, file_info: dict | None) -> None:
        conversation = self.get_or_create(session_id)
        conversation.set_uploaded_file(file_info)

    def get_uploaded_file(self, session_id: str) -> dict | None:
        conversation = self.sessions.get(session_id)
        if conversation and conversation.uploaded_file:
            return conversation.uploaded_file

        file_info = get_uploaded_file_info(session_id)
        if conversation and file_info:
            conversation.set_uploaded_file(file_info)

        return file_info

    def get_context(self, session_id: str, max_messages: int = 20) -> list[dict[str, str]]:
        conversation = self.sessions.get(session_id)
        if not conversation:
            return []
        return conversation.get_openai_messages(max_messages)

    def get_token_usage(self, session_id: str) -> dict:
        conversation = self.sessions.get(session_id)
        if not conversation:
            return {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "calls": 0,
            }
        return conversation.token_usage.to_dict()

    def get_pending_action(self, session_id: str) -> dict | None:
        conversation = self.sessions.get(session_id)
        if not conversation:
            return None
        return conversation.pending_action

    def set_pending_action(self, session_id: str, pending_action: dict | None) -> None:
        conversation = self.get_or_create(session_id)
        conversation.set_pending_action(pending_action)

    def clear_pending_action(self, session_id: str) -> None:
        conversation = self.sessions.get(session_id)
        if conversation:
            conversation.clear_pending_action()

    def delete_session(self, session_id: str) -> bool:
        existed = session_id in self.sessions
        self.sessions.pop(session_id, None)
        delete_session_uploads(session_id)
        return existed or get_uploaded_file_info(session_id) is not None


session_store = SessionStore()
