from datetime import datetime

from app.core.token_usage import TokenUsage


class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }

    def to_openai_format(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class Conversation:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: list[Message] = []
        self.created_at = datetime.utcnow().isoformat()
        self.token_usage = TokenUsage()
        self.uploaded_file: dict | None = None
        self.pending_action: dict | None = None

    def add_message(self, role: str, content: str) -> None:
        self.messages.append(Message(role, content))

    def add_token_usage(self, usage: dict) -> None:
        self.token_usage.add_from_dict(usage)

    def set_uploaded_file(self, file_info: dict | None) -> None:
        self.uploaded_file = file_info

    def set_pending_action(self, pending_action: dict | None) -> None:
        self.pending_action = pending_action

    def clear_pending_action(self) -> None:
        self.pending_action = None

    def get_openai_messages(self, max_messages: int = 20) -> list[dict[str, str]]:
        return [m.to_openai_format() for m in self.messages[-max_messages:]]
