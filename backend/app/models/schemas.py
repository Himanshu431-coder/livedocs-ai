from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from typing import Any

class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    SYNTHESIZER = "synthesizer"
    VERIFIER = "verifier"

class QueryComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ANALYTICAL = "analytical"

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class DocumentMeta(BaseModel):
    filename: str
    size_bytes: int
    modified_at: datetime
    chunk_count: int = 0
    doc_type: str = "txt"

class DocumentCreate(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    workspace: str = "default"

    @field_validator("filename")
    @classmethod
    def sanitize_filename(cls, v: str) -> str:
        v = v.strip()
        if not any(v.endswith(ext) for ext in [".txt", ".md", ".csv", ".json"]):
            v += ".txt"
        if "/" in v or "\\" in v or ".." in v:
            raise ValueError("Invalid filename")
        return v

class DocumentListResponse(BaseModel):
    documents: list[DocumentMeta]
    total: int
    workspace: str

class Citation(BaseModel):
    source_file: str
    chunk_text: str
    relevance_score: float
    chunk_index: int

class AgentStep(BaseModel):
    agent: AgentRole
    action: str
    thought: str
    result: str
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    workspace: str = "default"
    conversation_id: str | None = None
    stream: bool = False
    include_citations: bool = True
    complexity: QueryComplexity | None = None
    agent_mode: bool = True

class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    agent_trace: list[AgentStep] = []
    complexity: QueryComplexity
    total_latency_ms: float
    documents_searched: int
    chunks_retrieved: int
    model_used: str
    conversation_id: str
    confidence_score: float = 0.0

class ConversationMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = {}

class Conversation(BaseModel):
    id: str
    workspace: str
    messages: list[ConversationMessage] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    summary: str = ""
