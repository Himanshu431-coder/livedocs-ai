import uuid
from datetime import datetime
from app.models.schemas import Conversation, ConversationMessage, MessageRole
from app.core.llm import get_llm
from app.config import get_settings

class ConversationMemory:
    def __init__(self):
        self.settings = get_settings()
        self._conversations: dict[str, Conversation] = {}

    def create(self, workspace: str = "default") -> str:
        conv_id = str(uuid.uuid4())[:8]
        self._conversations[conv_id] = Conversation(id=conv_id, workspace=workspace)
        return conv_id

    def get(self, conv_id: str) -> Conversation | None:
        return self._conversations.get(conv_id)

    def add_message(self, conv_id: str, role: MessageRole, content: str, metadata: dict | None = None):
        conv = self._conversations.get(conv_id)
        if not conv:
            return
        conv.messages.append(ConversationMessage(role=role, content=content, metadata=metadata or {}))
        conv.updated_at = datetime.now()
        if len(conv.messages) > self.settings.max_conversation_turns * 2:
            self._summarize_and_compact(conv)

    def get_context_messages(self, conv_id: str, max_tokens: int | None = None) -> list[dict[str, str]]:
        conv = self._conversations.get(conv_id)
        if not conv:
            return []
        budget = max_tokens or self.settings.memory_window_tokens
        llm = get_llm()
        messages = []
        token_count = 0
        for msg in reversed(conv.messages):
            token_count += llm.count_tokens(msg.content)
            if token_count > budget:
                break
            messages.insert(0, {"role": msg.role.value, "content": msg.content})
        if len(messages) < len(conv.messages) and conv.summary:
            messages.insert(0, {"role": "system", "content": f"Previous conversation summary: {conv.summary}"})
        return messages

    def _summarize_and_compact(self, conv: Conversation):
        older = conv.messages[:len(conv.messages) // 2]
        older_text = "\n".join(f"{m.role.value}: {m.content[:200]}" for m in older)
        try:
            llm = get_llm()
            summary = llm.chat([
                {"role": "system", "content": "Summarize this conversation in 2-3 concise sentences."},
                {"role": "user", "content": older_text},
            ], max_tokens=200, temperature=0.0)
            conv.summary = summary
        except Exception:
            conv.summary = "Previous conversation context available."
        conv.messages = conv.messages[len(conv.messages) // 2:]

_memory: ConversationMemory | None = None

def get_memory() -> ConversationMemory:
    global _memory
    if _memory is None:
        _memory = ConversationMemory()
    return _memory
