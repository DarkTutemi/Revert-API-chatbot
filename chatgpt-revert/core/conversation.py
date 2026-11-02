"""
Per-client conversation state.
Maps x-session-id → ChatGPT conversation_id + parent_message_id
so follow-up messages continue the same upstream thread.
"""
import uuid
import threading


class ConversationStore:
    def __init__(self):
        self._states: dict[str, dict] = {}
        self._lock = threading.Lock()

    def get(self, session_id: str) -> dict:
        with self._lock:
            if session_id not in self._states:
                self._states[session_id] = {
                    "conversation_id": None,
                    "parent_message_id": str(uuid.uuid4()),
                }
            return self._states[session_id]

    def update(self, session_id: str, conversation_id, parent_message_id):
        with self._lock:
            self._states[session_id] = {
                "conversation_id": conversation_id,
                "parent_message_id": parent_message_id or str(uuid.uuid4()),
            }

    def reset(self, session_id: str):
        with self._lock:
            self._states.pop(session_id, None)

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._states)
