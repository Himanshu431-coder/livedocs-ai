import os

def w(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f'  OK  {path}')

print('=' * 60)
print('  LiveDocs AI v2 - Project Generator')
print('=' * 60)
print()

# ── ROOT FILES ──────────────────────────────────────────────

w('.gitignore', """
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
node_modules/
dist/
.vite/
data/workspaces/*/
!data/workspaces/default/
data/workspaces/default/.chroma/
.env
.vscode/
.idea/
.DS_Store
Thumbs.db
*.chroma/
""")

w('.env.example', """
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
LLM_MODEL=meta-llama/llama-3.3-70b-instruct:free
LLM_BASE_URL=https://openrouter.ai/api/v1/chat/completions
EMBEDDING_MODEL=all-MiniLM-L6-v2
HOST=0.0.0.0
PORT=8000
DEBUG=false
MCP_SERVER_NAME=livedocs-ai
MCP_SERVER_VERSION=2.0.0
DATA_DIR=./data/workspaces
DEFAULT_WORKSPACE=default
RATE_LIMIT_RPM=60
""")

w('.env', """
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
LLM_MODEL=meta-llama/llama-3.3-70b-instruct:free
LLM_BASE_URL=https://openrouter.ai/api/v1/chat/completions
EMBEDDING_MODEL=all-MiniLM-L6-v2
HOST=0.0.0.0
PORT=8000
DEBUG=false
MCP_SERVER_NAME=livedocs-ai
MCP_SERVER_VERSION=2.0.0
DATA_DIR=./data/workspaces
DEFAULT_WORKSPACE=default
RATE_LIMIT_RPM=60
""")

w('docker-compose.yml', """
version: "3.9"
services:
  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/data:/app/data
    env_file:
      - .env
    restart: unless-stopped
  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
""")

# ── BACKEND FILES ───────────────────────────────────────────

w('backend/requirements.txt', """
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
pydantic-settings==2.7.1
python-dotenv==1.0.1
openai==1.58.1
sentence-transformers==3.3.1
chromadb==0.5.23
numpy==1.26.4
rank-bm25==0.2.2
httpx==0.28.1
websockets==14.1
starlette==0.41.4
watchfiles==1.0.8
rich==13.9.4
tiktoken==0.9.0
tenacity==9.0.0
""")

w('backend/Dockerfile', """
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/data/workspaces/default
EXPOSE 8000
CMD ["python", "run.py"]
""")

w('backend/run.py', """
import uvicorn
from app.config import get_settings

def main():
    settings = get_settings()
    print()
    print("=" * 60)
    print("  LiveDocs AI v2.0")
    print("  Agentic Knowledge Intelligence Platform")
    print("  Agents - MCP - Real-Time")
    print("=" * 60)
    print()
    print(f"  API:  http://{settings.host}:{settings.port}/api/v1")
    print(f"  MCP:  http://{settings.host}:{settings.port}/mcp")
    print(f"  Docs: http://{settings.host}:{settings.port}/docs")
    print()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )

if __name__ == "__main__":
    main()
""")

# ── __init__.py files ───────────────────────────────────────

for d in ['backend/app', 'backend/app/models', 'backend/app/core',
          'backend/app/rag', 'backend/app/agents', 'backend/app/mcp',
          'backend/app/api']:
    w(f'{d}/__init__.py', '')

# ── CONFIG ──────────────────────────────────────────────────

w('backend/app/config.py', """
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from functools import lru_cache

class Settings(BaseSettings):
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    llm_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    llm_base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.1
    llm_timeout: int = 90
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_top_k: int = 8
    rerank_top_n: int = 4
    hybrid_alpha: float = 0.7
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    mcp_server_name: str = "livedocs-ai"
    mcp_server_version: str = "2.0.0"
    data_dir: Path = Path("./data/workspaces")
    default_workspace: str = "default"
    rate_limit_rpm: int = 60
    max_conversation_turns: int = 20
    memory_window_tokens: int = 4096

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def get_workspace_dir(self, workspace: str | None = None) -> Path:
        ws = workspace or self.default_workspace
        path = self.data_dir / ws
        path.mkdir(parents=True, exist_ok=True)
        return path

@lru_cache()
def get_settings() -> Settings:
    return Settings()
""")

# ── SCHEMAS ─────────────────────────────────────────────────

w('backend/app/models/schemas.py', """
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
        if "/" in v or "\\\\" in v or ".." in v:
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
""")

# ── LLM CLIENT ──────────────────────────────────────────────

w('backend/app/core/llm.py', """
import requests
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings
from typing import Generator

class LLMClient:
    def __init__(self):
        self.settings = get_settings()
        self._encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self._encoding.encode(text))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    def chat(self, messages: list[dict], temperature: float | None = None,
             max_tokens: int | None = None, json_mode: bool = False) -> str:
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://livedocs-ai.app",
            "X-Title": "LiveDocs AI v2",
        }
        payload = {
            "model": self.settings.llm_model,
            "messages": messages,
            "max_tokens": max_tokens or self.settings.llm_max_tokens,
            "temperature": temperature or self.settings.llm_temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        response = requests.post(
            self.settings.llm_base_url, headers=headers,
            json=payload, timeout=self.settings.llm_timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def chat_stream(self, messages: list[dict], temperature: float | None = None) -> Generator[str, None, None]:
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://livedocs-ai.app",
            "X-Title": "LiveDocs AI v2",
        }
        payload = {
            "model": self.settings.llm_model,
            "messages": messages,
            "max_tokens": self.settings.llm_max_tokens,
            "temperature": temperature or self.settings.llm_temperature,
            "stream": True,
        }
        with requests.post(self.settings.llm_base_url, headers=headers, json=payload, timeout=self.settings.llm_timeout, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        import json
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

    def classify_complexity(self, question: str) -> str:
        messages = [
            {"role": "system", "content": "Classify the query complexity. Respond with ONLY one word: simple, moderate, complex, or analytical.\\n\\nsimple = single fact lookup\\nmoderate = requires 1-2 document sections\\ncomplex = requires cross-document synthesis\\nanalytical = requires deep reasoning, comparison, or computation"},
            {"role": "user", "content": question},
        ]
        result = self.chat(messages, max_tokens=10, temperature=0.0)
        return result.strip().lower()

_llm_client: LLMClient | None = None

def get_llm() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
""")

# ── MEMORY ──────────────────────────────────────────────────

w('backend/app/core/memory.py', """
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
        older_text = "\\n".join(f"{m.role.value}: {m.content[:200]}" for m in older)
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
""")

# ── WATCHER ─────────────────────────────────────────────────

w('backend/app/core/watcher.py', """
import asyncio
from pathlib import Path
from watchfiles import awatch
from app.config import get_settings
from app.rag.engine import get_rag_engine
from rich.console import Console

console = Console()

class FileWatcher:
    def __init__(self):
        self.settings = get_settings()
        self._running = False

    async def start(self, workspace: str = "default"):
        watch_dir = self.settings.get_workspace_dir(workspace)
        self._running = True
        console.print(f"[bold green]Watching:[/bold green] {watch_dir}")
        async for changes in awatch(watch_dir):
            if not self._running:
                break
            engine = get_rag_engine(workspace)
            for change_type, path in changes:
                filepath = Path(path)
                if not filepath.is_file():
                    continue
                if filepath.suffix not in [".txt", ".md", ".csv", ".json"]:
                    continue
                filename = filepath.name
                console.print(f"[yellow]{change_type.name}:[/yellow] {filename}")
                if change_type.name in ("added", "modified"):
                    await engine.ingest_file(filepath, workspace)
                    console.print(f"[green]Indexed:[/green] {filename}")
                elif change_type.name == "deleted":
                    await engine.remove_file(filename, workspace)
                    console.print(f"[red]Removed:[/red] {filename}")

    def stop(self):
        self._running = False

_watcher: FileWatcher | None = None

def get_watcher() -> FileWatcher:
    global _watcher
    if _watcher is None:
        _watcher = FileWatcher()
    return _watcher
""")

# ── CHUNKER ─────────────────────────────────────────────────

w('backend/app/rag/chunker.py', """
from dataclasses import dataclass
from app.config import get_settings

@dataclass
class Chunk:
    text: str
    source_file: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict

class SemanticChunker:
    def __init__(self):
        self.settings = get_settings()

    def chunk_text(self, text: str, source_file: str, metadata: dict | None = None) -> list[Chunk]:
        chunk_size = self.settings.chunk_size
        overlap = self.settings.chunk_overlap
        metadata = metadata or {}
        paragraphs = [p.strip() for p in text.split("\\n\\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text.strip()]
        chunks = []
        current_text = ""
        chunk_idx = 0
        char_offset = 0
        for para in paragraphs:
            if len(current_text) + len(para) > chunk_size and current_text:
                chunks.append(Chunk(
                    text=current_text.strip(), source_file=source_file,
                    chunk_index=chunk_idx, start_char=char_offset,
                    end_char=char_offset + len(current_text), metadata={**metadata},
                ))
                chunk_idx += 1
                char_offset += len(current_text) - overlap
                overlap_text = current_text[-overlap:] if overlap > 0 else ""
                current_text = overlap_text + "\\n\\n" + para
            else:
                current_text = (current_text + "\\n\\n" + para) if current_text else para
        if current_text.strip():
            chunks.append(Chunk(
                text=current_text.strip(), source_file=source_file,
                chunk_index=chunk_idx, start_char=char_offset,
                end_char=char_offset + len(current_text), metadata={**metadata},
            ))
        return chunks

    def chunk_file(self, filepath: str, source_file: str | None = None) -> list[Chunk]:
        from pathlib import Path
        path = Path(filepath)
        source = source_file or path.name
        text = path.read_text(encoding="utf-8", errors="replace")
        meta = {"file_size": path.stat().st_size, "file_type": path.suffix, "modified": path.stat().st_mtime}
        return self.chunk_text(text, source, meta)
""")

# ── VECTOR STORE ────────────────────────────────────────────

w('backend/app/rag/vectorstore.py', """
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import numpy as np
from typing import Any
from app.config import get_settings
from app.rag.chunker import Chunk

class HybridVectorStore:
    def __init__(self, workspace: str = "default"):
        self.settings = get_settings()
        self.workspace = workspace
        self.embedder = SentenceTransformer(self.settings.embedding_model)
        self._client = chromadb.Client(ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(self.settings.data_dir / workspace / ".chroma"),
            anonymized_telemetry=False,
        ))
        self._collection = self._client.get_or_create_collection(
            name=f"livedocs_{workspace}", metadata={"hnsw:space": "cosine"},
        )
        self._bm25: BM25Okapi | None = None
        self._bm25_chunks: list[Chunk] = []
        self._all_chunks: list[Chunk] = []

    def add_chunks(self, chunks: list[Chunk]):
        if not chunks:
            return
        texts = [c.text for c in chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=False).tolist()
        ids = [f"{c.source_file}::{c.chunk_index}" for c in chunks]
        metadatas = [{"source_file": c.source_file, "chunk_index": c.chunk_index, "start_char": c.start_char, "end_char": c.end_char} for c in chunks]
        self._collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        self._all_chunks.extend(chunks)
        self._rebuild_bm25()

    def remove_file(self, filename: str):
        self._collection.delete(where={"source_file": filename})
        self._all_chunks = [c for c in self._all_chunks if c.source_file != filename]
        self._rebuild_bm25()

    def search(self, query: str, top_k: int | None = None) -> list[tuple[Chunk, float]]:
        top_k = top_k or self.settings.retrieval_top_k
        alpha = self.settings.hybrid_alpha
        query_embedding = self.embedder.encode([query], show_progress_bar=False).tolist()
        dense_results = self._collection.query(
            query_embeddings=query_embedding, n_results=min(top_k * 3, 50),
            include=["documents", "metadatas", "distances"],
        )
        dense_ranked: dict[str, tuple[Chunk, float]] = {}
        if dense_results and dense_results["ids"][0]:
            for i, doc_id in enumerate(dense_results["ids"][0]):
                dist = dense_results["distances"][0][i]
                meta = dense_results["metadatas"][0][i]
                chunk = Chunk(
                    text=dense_results["documents"][0][i], source_file=meta["source_file"],
                    chunk_index=meta["chunk_index"], start_char=meta["start_char"],
                    end_char=meta["end_char"], metadata=meta,
                )
                dense_ranked[doc_id] = (chunk, 1.0 - dist)
        sparse_ranked: dict[str, tuple[Chunk, float]] = {}
        if self._bm25 is not None and self._bm25_chunks:
            tokenized_query = query.lower().split()
            scores = self._bm25.get_scores(tokenized_query)
            top_indices = np.argsort(scores)[::-1][:top_k * 3]
            for rank, idx in enumerate(top_indices):
                if scores[idx] > 0:
                    chunk = self._bm25_chunks[idx]
                    doc_id = f"{chunk.source_file}::{chunk.chunk_index}"
                    sparse_ranked[doc_id] = (chunk, float(scores[idx]))
        k = 60
        fused_scores: dict[str, float] = {}
        chunk_map: dict[str, Chunk] = {}
        for rank, (doc_id, (chunk, _)) in enumerate(dense_ranked.items()):
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + alpha / (k + rank + 1)
            chunk_map[doc_id] = chunk
        for rank, (doc_id, (chunk, _)) in enumerate(sparse_ranked.items()):
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + (1 - alpha) / (k + rank + 1)
            chunk_map[doc_id] = chunk
        sorted_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)[:top_k]
        return [(chunk_map[doc_id], fused_scores[doc_id]) for doc_id in sorted_ids]

    def get_stats(self) -> dict[str, Any]:
        count = self._collection.count()
        files = set(c.source_file for c in self._all_chunks)
        return {"total_chunks": count, "total_documents": len(files), "documents": list(files), "bm25_indexed": self._bm25 is not None}

    def _rebuild_bm25(self):
        if not self._all_chunks:
            self._bm25 = None
            self._bm25_chunks = []
            return
        self._bm25_chunks = list(self._all_chunks)
        tokenized = [c.text.lower().split() for c in self._bm25_chunks]
        self._bm25 = BM25Okapi(tokenized)
""")

# ── RAG ENGINE ──────────────────────────────────────────────

w('backend/app/rag/engine.py', """
import time
import json
from pathlib import Path
from app.config import get_settings
from app.rag.chunker import SemanticChunker, Chunk
from app.rag.vectorstore import HybridVectorStore
from app.core.llm import get_llm
from app.models.schemas import Citation

class RAGEngine:
    def __init__(self, workspace: str = "default"):
        self.settings = get_settings()
        self.workspace = workspace
        self.chunker = SemanticChunker()
        self.store = HybridVectorStore(workspace)
        self.llm = get_llm()

    async def ingest_file(self, filepath: Path, workspace: str | None = None):
        chunks = self.chunker.chunk_file(str(filepath))
        if chunks:
            self.store.remove_file(filepath.name)
            self.store.add_chunks(chunks)

    async def remove_file(self, filename: str, workspace: str | None = None):
        self.store.remove_file(filename)

    async def ingest_workspace(self):
        ws_dir = self.settings.get_workspace_dir(self.workspace)
        for filepath in ws_dir.glob("*"):
            if filepath.suffix in [".txt", ".md", ".csv", ".json"]:
                await self.ingest_file(filepath)

    async def retrieve(self, query: str, top_k: int | None = None) -> list[tuple[Chunk, float]]:
        return self.store.search(query, top_k=top_k or self.settings.retrieval_top_k)

    async def rerank(self, query: str, results: list[tuple[Chunk, float]], top_n: int | None = None) -> list[tuple[Chunk, float]]:
        top_n = top_n or self.settings.rerank_top_n
        if len(results) <= top_n:
            return results
        chunks_text = ""
        for i, (chunk, score) in enumerate(results):
            chunks_text += f"\\n[CHUNK {i}] (score: {score:.4f})\\n{chunk.text[:300]}\\n"
        try:
            response = self.llm.chat([
                {"role": "system", "content": "You are a relevance ranking engine. Return only a JSON array of integers."},
                {"role": "user", "content": f'Given the query: "{query}"\\n\\nRank these chunks by relevance (most relevant first). Return ONLY a JSON array of chunk indices.\\n\\nChunks:{chunks_text}\\nRanked indices:'},
            ], max_tokens=200, temperature=0.0, json_mode=True)
            ranked_indices = json.loads(response)
            reranked = []
            for idx in ranked_indices[:top_n]:
                if 0 <= idx < len(results):
                    reranked.append(results[idx])
            for r in results:
                if r not in reranked:
                    reranked.append(r)
            return reranked[:top_n]
        except Exception:
            return results[:top_n]

    async def generate(self, query: str, chunks: list[tuple[Chunk, float]], conversation_history: list[dict] | None = None) -> str:
        context_parts = []
        for i, (chunk, score) in enumerate(chunks):
            context_parts.append(f"[Source: {chunk.source_file}, Chunk {chunk.chunk_index}, Relevance: {score:.4f}]\\n{chunk.text}")
        context = "\\n\\n---\\n\\n".join(context_parts)
        system_prompt = "You are LiveDocs AI, an advanced knowledge intelligence assistant.\\nRULES:\\n1. Answer based ONLY on the provided document chunks.\\n2. Cite sources using [Source: filename] format.\\n3. If the answer is not in the documents, say: I don't have sufficient information in the current knowledge base to answer this question.\\n4. Be precise, structured, and comprehensive.\\n5. Use markdown formatting for clarity.\\n6. If multiple sources contribute, synthesize them."
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history[-6:])
        messages.append({"role": "user", "content": f"Document Chunks:\\n{context}\\n\\n---\\n\\nQuestion: {query}\\n\\nProvide a comprehensive answer with citations:"})
        return self.llm.chat(messages)

    async def query(self, question: str, conversation_history: list[dict] | None = None) -> dict:
        start = time.time()
        results = await self.retrieve(question)
        if not results:
            return {"answer": "No documents found in the knowledge base. Please add documents first.", "citations": [], "chunks_retrieved": 0, "latency_ms": (time.time() - start) * 1000}
        reranked = await self.rerank(question, results)
        answer = await self.generate(question, reranked, conversation_history)
        citations = [Citation(source_file=c.source_file, chunk_text=c.text[:200] + "...", relevance_score=round(s, 4), chunk_index=c.chunk_index) for c, s in reranked]
        return {"answer": answer, "citations": citations, "chunks_retrieved": len(reranked), "latency_ms": (time.time() - start) * 1000}

    def get_stats(self) -> dict:
        return self.store.get_stats()

_engines: dict[str, RAGEngine] = {}

def get_rag_engine(workspace: str = "default") -> RAGEngine:
    if workspace not in _engines:
        _engines[workspace] = RAGEngine(workspace)
    return _engines[workspace]
""")

# ── AGENT TOOLS ─────────────────────────────────────────────

w('backend/app/agents/tools.py', """
import time
import json
from app.rag.engine import get_rag_engine
from app.core.llm import get_llm

async def tool_search_documents(query: str, workspace: str = "default", top_k: int = 6) -> dict:
    start = time.time()
    engine = get_rag_engine(workspace)
    results = await engine.retrieve(query, top_k=top_k)
    return {
        "chunks": [{"source": c.source_file, "text": c.text, "score": round(s, 4), "chunk_index": c.chunk_index} for c, s in results],
        "total_found": len(results),
        "latency_ms": (time.time() - start) * 1000,
    }

async def tool_analyze_findings(question: str, chunks: list[dict]) -> dict:
    start = time.time()
    llm = get_llm()
    chunks_text = "\\n\\n".join(f"[{c['source']}]\\n{c['text']}" for c in chunks[:8])
    analysis = llm.chat([
        {"role": "system", "content": "You are a document analyst. Given a question and document excerpts:\\n1. Extract KEY FACTS relevant to the question\\n2. Identify any CONTRADICTIONS between sources\\n3. Note INFORMATION GAPS (what is missing)\\n4. Rate your CONFIDENCE (0.0-1.0)\\n\\nRespond in JSON format:\\n{\\\"key_facts\\\": [...], \\\"contradictions\\\": [...], \\\"gaps\\\": [...], \\\"confidence\\\": 0.0}"},
        {"role": "user", "content": f"Question: {question}\\n\\nExcerpts:\\n{chunks_text}"},
    ], max_tokens=500, temperature=0.0, json_mode=True)
    try:
        result = json.loads(analysis)
    except json.JSONDecodeError:
        result = {"key_facts": [], "contradictions": [], "gaps": ["Analysis parsing failed"], "confidence": 0.3}
    result["latency_ms"] = (time.time() - start) * 1000
    return result

async def tool_synthesize_answer(question: str, chunks: list[dict], analysis: dict) -> dict:
    start = time.time()
    llm = get_llm()
    chunks_text = "\\n\\n".join(f"[{c['source']}]\\n{c['text']}" for c in chunks[:6])
    answer = llm.chat([
        {"role": "system", "content": "You are LiveDocs AI, an advanced knowledge intelligence assistant.\\nSynthesize a comprehensive, well-structured answer using the provided chunks and analysis. Cite sources as [Source: filename]. Use markdown formatting. Be precise and thorough."},
        {"role": "user", "content": f"Question: {question}\\n\\nKey Facts: {analysis.get('key_facts', [])}\\nConfidence: {analysis.get('confidence', 0.5)}\\n\\nSource Chunks:\\n{chunks_text}"},
    ], max_tokens=1500, temperature=0.1)
    return {"answer": answer, "confidence": analysis.get("confidence", 0.5), "latency_ms": (time.time() - start) * 1000}

async def tool_verify_answer(question: str, answer: str, chunks: list[dict]) -> dict:
    start = time.time()
    llm = get_llm()
    chunks_text = "\\n\\n".join(f"[{c['source']}]\\n{c['text'][:200]}" for c in chunks[:4])
    verification = llm.chat([
        {"role": "system", "content": "You are a fact-checker. Verify if the answer is fully supported by the source documents. Respond in JSON:\\n{\\\"verified\\\": true/false, \\\"issues\\\": [...], \\\"accuracy_score\\\": 0.0-1.0, \\\"suggested_fix\\\": \\\"...\\\"}"},
        {"role": "user", "content": f"Question: {question}\\n\\nAnswer: {answer}\\n\\nSources:\\n{chunks_text}"},
    ], max_tokens=300, temperature=0.0, json_mode=True)
    try:
        result = json.loads(verification)
    except json.JSONDecodeError:
        result = {"verified": True, "issues": [], "accuracy_score": 0.7, "suggested_fix": ""}
    result["latency_ms"] = (time.time() - start) * 1000
    return result

async def tool_extract_insights(workspace: str = "default") -> dict:
    start = time.time()
    llm = get_llm()
    engine = get_rag_engine(workspace)
    all_chunks = engine.store._all_chunks
    if not all_chunks:
        return {"insights": [], "latency_ms": 0}
    sample_chunks = []
    seen_files = set()
    for chunk in all_chunks:
        if chunk.source_file not in seen_files:
            sample_chunks.append(chunk)
            seen_files.add(chunk.source_file)
    chunks_text = "\\n\\n".join(f"[{c.source_file}]\\n{c.text[:400]}" for c in sample_chunks[:10])
    insights = llm.chat([
        {"role": "system", "content": "Analyze these document excerpts and extract:\\n1. KEY INSIGHTS\\n2. ENTITIES (people, orgs, projects, metrics)\\n3. RELATIONSHIPS\\n4. KNOWLEDGE GAPS\\n\\nRespond in JSON:\\n{\\\"insights\\\": [...], \\\"entities\\\": [...], \\\"relationships\\\": [...], \\\"gaps\\\": [...]}"},
        {"role": "user", "content": chunks_text},
    ], max_tokens=600, temperature=0.1, json_mode=True)
    try:
        result = json.loads(insights)
    except json.JSONDecodeError:
        result = {"insights": [], "entities": [], "relationships": [], "gaps": []}
    result["latency_ms"] = (time.time() - start) * 1000
    return result
""")

# ── ORCHESTRATOR ────────────────────────────────────────────

w('backend/app/agents/orchestrator.py', """
import time
from app.core.llm import get_llm
from app.core.memory import get_memory
from app.agents.tools import tool_search_documents, tool_analyze_findings, tool_synthesize_answer, tool_verify_answer
from app.models.schemas import AgentStep, AgentRole, QueryComplexity, QueryResponse, Citation, MessageRole

class AgentOrchestrator:
    def __init__(self, workspace: str = "default"):
        self.workspace = workspace
        self.llm = get_llm()
        self.memory = get_memory()

    async def run(self, question: str, conversation_id: str | None = None, stream: bool = False) -> QueryResponse:
        start_time = time.time()
        trace: list[AgentStep] = []
        if not conversation_id:
            conversation_id = self.memory.create(self.workspace)
        conv = self.memory.get(conversation_id)
        if not conv:
            conversation_id = self.memory.create(self.workspace)

        # Step 1: Classify
        t0 = time.time()
        complexity_str = self.llm.classify_complexity(question)
        try:
            complexity = QueryComplexity(complexity_str)
        except ValueError:
            complexity = QueryComplexity.MODERATE
        trace.append(AgentStep(agent=AgentRole.ORCHESTRATOR, action="classify", thought="Determining query complexity...", result=f"Complexity: {complexity.value}", latency_ms=(time.time() - t0) * 1000))

        # Step 2: Plan
        plan = self._plan_agents(complexity)
        trace.append(AgentStep(agent=AgentRole.ORCHESTRATOR, action="plan", thought=f"Query is {complexity.value}, planning agent pipeline", result=f"Pipeline: {' -> '.join(plan)}", latency_ms=0))

        # Step 3: Research
        t0 = time.time()
        search_result = await tool_search_documents(question, self.workspace)
        chunks = search_result["chunks"]
        trace.append(AgentStep(agent=AgentRole.RESEARCHER, action="search", thought="Searching knowledge base...", result=f"Found {len(chunks)} relevant chunks", latency_ms=search_result["latency_ms"]))

        if not chunks:
            return QueryResponse(answer="No relevant information found in the knowledge base.", citations=[], agent_trace=trace, complexity=complexity, total_latency_ms=(time.time() - start_time) * 1000, documents_searched=0, chunks_retrieved=0, model_used=self.llm.settings.llm_model, conversation_id=conversation_id, confidence_score=0.0)

        # Step 4: Analyze
        analysis = {}
        if "analyze" in plan:
            t0 = time.time()
            analysis = await tool_analyze_findings(question, chunks)
            trace.append(AgentStep(agent=AgentRole.ANALYST, action="analyze", thought="Extracting key facts and identifying gaps...", result=f"Facts: {len(analysis.get('key_facts', []))} | Gaps: {len(analysis.get('gaps', []))} | Confidence: {analysis.get('confidence', 0)}", latency_ms=analysis.get("latency_ms", 0)))

        # Step 5: Synthesize
        t0 = time.time()
        synth_result = await tool_synthesize_answer(question, chunks, analysis)
        answer = synth_result["answer"]
        confidence = synth_result.get("confidence", 0.5)
        trace.append(AgentStep(agent=AgentRole.SYNTHESIZER, action="synthesize", thought="Composing final answer with citations...", result=f"Answer generated ({len(answer)} chars, confidence: {confidence})", latency_ms=synth_result.get("latency_ms", 0)))

        # Step 6: Verify
        if "verify" in plan:
            t0 = time.time()
            verify_result = await tool_verify_answer(question, answer, chunks)
            if not verify_result.get("verified", True):
                fix = verify_result.get("suggested_fix", "")
                if fix:
                    answer += f"\\n\\n**Verification Note:** {fix}"
                confidence *= verify_result.get("accuracy_score", 0.8)
            trace.append(AgentStep(agent=AgentRole.VERIFIER, action="verify", thought="Fact-checking answer against sources...", result=f"Verified: {verify_result.get('verified', True)} | Accuracy: {verify_result.get('accuracy_score', 0):.2f}", latency_ms=verify_result.get("latency_ms", 0)))

        citations = [Citation(source_file=c["source"], chunk_text=c["text"][:200] + "...", relevance_score=c["score"], chunk_index=c["chunk_index"]) for c in chunks[:6]]
        self.memory.add_message(conversation_id, MessageRole.USER, question)
        self.memory.add_message(conversation_id, MessageRole.ASSISTANT, answer)
        total_latency = (time.time() - start_time) * 1000

        return QueryResponse(answer=answer, citations=citations, agent_trace=trace, complexity=complexity, total_latency_ms=total_latency, documents_searched=len(set(c["source"] for c in chunks)), chunks_retrieved=len(chunks), model_used=self.llm.settings.llm_model, conversation_id=conversation_id, confidence_score=round(confidence, 3))

    def _plan_agents(self, complexity: QueryComplexity) -> list[str]:
        plans = {
            QueryComplexity.SIMPLE: ["search", "synthesize"],
            QueryComplexity.MODERATE: ["search", "analyze", "synthesize"],
            QueryComplexity.COMPLEX: ["search", "analyze", "synthesize", "verify"],
            QueryComplexity.ANALYTICAL: ["search", "analyze", "synthesize", "verify"],
        }
        return plans.get(complexity, plans[QueryComplexity.MODERATE])
""")

# ── MCP PROTOCOL ────────────────────────────────────────────

w('backend/app/mcp/protocol.py', """
import json
from typing import Any

class MCPProtocol:
    def __init__(self, server_name: str, server_version: str):
        self.server_name = server_name
        self.server_version = server_version
        self._tools: dict[str, dict] = {}
        self._tool_handlers: dict[str, callable] = {}

    def register_tool(self, name: str, description: str, parameters: dict, handler: callable):
        self._tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": {
                "type": "object",
                "properties": parameters,
                "required": [k for k, v in parameters.items() if v.get("required", True)],
            },
        }
        self._tool_handlers[name] = handler

    async def handle_message(self, message: str) -> str | None:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return self._error(None, -32700, "Parse error")
        method = data.get("method", "")
        params = data.get("params", {})
        msg_id = data.get("id")
        if method == "initialize":
            return self._response(msg_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": self.server_name, "version": self.server_version}})
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return self._response(msg_id, {})
        if method == "tools/list":
            return self._response(msg_id, {"tools": list(self._tools.values())})
        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            if tool_name not in self._tool_handlers:
                return self._error(msg_id, -32601, f"Tool not found: {tool_name}")
            try:
                result = await self._tool_handlers[tool_name](**arguments)
                return self._response(msg_id, {"content": [{"type": "text", "text": json.dumps(result, default=str) if isinstance(result, dict) else str(result)}]})
            except Exception as e:
                return self._error(msg_id, -32603, f"Tool execution error: {str(e)}")
        return self._error(msg_id, -32601, f"Method not found: {method}")

    def _response(self, msg_id: Any, result: Any) -> str:
        return json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result})

    def _error(self, msg_id: Any, code: int, message: str) -> str:
        return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}})

    def get_tool_manifest(self) -> dict:
        return {"server": {"name": self.server_name, "version": self.server_version}, "tools": list(self._tools.values()), "tool_count": len(self._tools)}
""")

# ── MCP SERVER ──────────────────────────────────────────────

w('backend/app/mcp/server.py', """
from app.config import get_settings
from app.mcp.protocol import MCPProtocol
from app.agents.tools import tool_search_documents, tool_analyze_findings, tool_extract_insights
from app.rag.engine import get_rag_engine

def create_mcp_server() -> MCPProtocol:
    settings = get_settings()
    server = MCPProtocol(server_name=settings.mcp_server_name, server_version=settings.mcp_server_version)

    server.register_tool("search_documents", "Search the knowledge base using hybrid semantic + keyword search with reciprocal rank fusion.", {
        "query": {"type": "string", "description": "The search query", "required": True},
        "workspace": {"type": "string", "description": "Workspace (default: default)", "required": False},
        "top_k": {"type": "integer", "description": "Number of results (default: 6)", "required": False},
    }, _mcp_search)

    server.register_tool("get_document", "Retrieve full content of a specific document by filename.", {
        "filename": {"type": "string", "description": "Document filename", "required": True},
        "workspace": {"type": "string", "description": "Workspace (default: default)", "required": False},
    }, _mcp_get_document)

    server.register_tool("list_documents", "List all documents in the knowledge base with metadata.", {
        "workspace": {"type": "string", "description": "Workspace (default: default)", "required": False},
    }, _mcp_list_documents)

    server.register_tool("add_document", "Add a new document to the knowledge base. Instantly indexed.", {
        "filename": {"type": "string", "description": "Filename", "required": True},
        "content": {"type": "string", "description": "Document content", "required": True},
        "workspace": {"type": "string", "description": "Workspace (default: default)", "required": False},
    }, _mcp_add_document)

    server.register_tool("extract_insights", "Auto-extract key insights, entities, relationships, and knowledge gaps across all documents.", {
        "workspace": {"type": "string", "description": "Workspace (default: default)", "required": False},
    }, _mcp_extract_insights)

    server.register_tool("analyze_query", "Deep analysis of retrieved information. Extracts key facts, contradictions, and gaps.", {
        "query": {"type": "string", "description": "Query to analyze", "required": True},
        "workspace": {"type": "string", "description": "Workspace (default: default)", "required": False},
    }, _mcp_analyze)

    return server

async def _mcp_search(query: str, workspace: str = "default", top_k: int = 6):
    return await tool_search_documents(query, workspace, top_k)

async def _mcp_get_document(filename: str, workspace: str = "default"):
    from app.config import get_settings
    from pathlib import Path
    settings = get_settings()
    filepath = settings.get_workspace_dir(workspace) / filename
    if not filepath.exists():
        return {"error": f"Document not found: {filename}"}
    return {"filename": filename, "content": filepath.read_text(encoding="utf-8"), "size_bytes": filepath.stat().st_size}

async def _mcp_list_documents(workspace: str = "default"):
    return get_rag_engine(workspace).get_stats()

async def _mcp_add_document(filename: str, content: str, workspace: str = "default"):
    from app.config import get_settings
    from pathlib import Path
    settings = get_settings()
    filepath = settings.get_workspace_dir(workspace) / filename
    filepath.write_text(content, encoding="utf-8")
    engine = get_rag_engine(workspace)
    await engine.ingest_file(filepath, workspace)
    return {"status": "indexed", "filename": filename}

async def _mcp_extract_insights(workspace: str = "default"):
    return await tool_extract_insights(workspace)

async def _mcp_analyze(query: str, workspace: str = "default"):
    search_result = await tool_search_documents(query, workspace)
    chunks = search_result["chunks"]
    if not chunks:
        return {"error": "No relevant documents found"}
    return await tool_analyze_findings(query, chunks)
""")

# ── API ROUTES ──────────────────────────────────────────────

w('backend/app/api/routes.py', """
import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse, DocumentCreate, DocumentMeta, DocumentListResponse
from app.agents.orchestrator import AgentOrchestrator
from app.rag.engine import get_rag_engine
from app.config import get_settings

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(req: QueryRequest):
    orchestrator = AgentOrchestrator(workspace=req.workspace)
    return await orchestrator.run(question=req.question, conversation_id=req.conversation_id, stream=req.stream)

@router.post("/query/simple")
async def simple_query(question: str, workspace: str = "default"):
    engine = get_rag_engine(workspace)
    return await engine.query(question)

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(workspace: str = "default"):
    settings = get_settings()
    ws_dir = settings.get_workspace_dir(workspace)
    docs = []
    for filepath in sorted(ws_dir.glob("*")):
        if filepath.suffix in [".txt", ".md", ".csv", ".json"] and filepath.is_file():
            stat = filepath.stat()
            docs.append(DocumentMeta(filename=filepath.name, size_bytes=stat.st_size, modified_at=datetime.fromtimestamp(stat.st_mtime), doc_type=filepath.suffix[1:]))
    return DocumentListResponse(documents=docs, total=len(docs), workspace=workspace)

@router.post("/documents")
async def add_document(req: DocumentCreate):
    settings = get_settings()
    ws_dir = settings.get_workspace_dir(req.workspace)
    filepath = ws_dir / req.filename
    filepath.write_text(req.content, encoding="utf-8")
    engine = get_rag_engine(req.workspace)
    await engine.ingest_file(filepath, req.workspace)
    return {"status": "indexed", "filename": req.filename, "workspace": req.workspace, "size_bytes": len(req.content.encode())}

@router.delete("/documents/{filename}")
async def delete_document(filename: str, workspace: str = "default"):
    settings = get_settings()
    filepath = settings.get_workspace_dir(workspace) / filename
    if not filepath.exists():
        raise HTTPException(404, f"Document not found: {filename}")
    filepath.unlink()
    engine = get_rag_engine(workspace)
    await engine.remove_file(filename, workspace)
    return {"status": "deleted", "filename": filename}

@router.get("/analytics/stats")
async def get_stats(workspace: str = "default"):
    return get_rag_engine(workspace).get_stats()

@router.get("/mcp/manifest")
async def mcp_manifest():
    from app.mcp.server import create_mcp_server
    return create_mcp_server().get_tool_manifest()

@router.post("/mcp/call")
async def mcp_call(tool_name: str, arguments: dict):
    from app.mcp.server import create_mcp_server
    server = create_mcp_server()
    message = json.dumps({"method": "tools/call", "params": {"name": tool_name, "arguments": arguments}, "id": 1})
    response = await server.handle_message(message)
    if response:
        return json.loads(response)
    raise HTTPException(500, "MCP call failed")

@router.get("/health")
async def health():
    return {"status": "healthy", "service": "LiveDocs AI", "version": "2.0.0", "timestamp": datetime.now().isoformat()}
""")

# ── MAIN APP ────────────────────────────────────────────────

w('backend/app/main.py', """
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from app.config import get_settings
from app.api.routes import router
from app.rag.engine import get_rag_engine
from app.core.watcher import get_watcher
from rich.console import Console

console = Console()

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    console.print("[bold cyan]LiveDocs AI v2.0 - Starting...[/bold cyan]")
    for ws_dir in settings.data_dir.iterdir():
        if ws_dir.is_dir() and not ws_dir.name.startswith("."):
            engine = get_rag_engine(ws_dir.name)
            await engine.ingest_workspace()
            stats = engine.get_stats()
            console.print(f"  [green]{ws_dir.name}:[/green] {stats['total_documents']} docs, {stats['total_chunks']} chunks")
    watcher = get_watcher()
    watcher_task = asyncio.create_task(watcher.start())
    console.print("[bold green]Ready![/bold green]")
    yield
    watcher.stop()
    watcher_task.cancel()

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="LiveDocs AI",
        description="Agentic Knowledge Intelligence Platform - Multi-Agent RAG + MCP Server + Real-Time Document Intelligence",
        version="2.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.include_router(router, prefix="/api/v1")

    @app.post("/mcp")
    async def mcp_endpoint(message: str):
        from app.mcp.server import create_mcp_server
        server = create_mcp_server()
        response = await server.handle_message(message)
        if response:
            return json.loads(response)
        return {"status": "ok"}

    return app

app = create_app()
""")

# ── SAMPLE DOCUMENTS ────────────────────────────────────────

w('backend/data/workspaces/default/company_profile.txt', """
TECHVENTURE INC. - COMPANY PROFILE
=====================================
Company Name: TechVenture Inc.
Industry: Artificial Intelligence & Machine Learning
Founded: 2020
Headquarters: San Francisco, California, USA

LEADERSHIP TEAM:
- CEO: Dr. Sarah Chen (Ph.D. Stanford, AI Research)
- CTO: Marcus Johnson (Former Google Brain)
- CFO: Rebecca Williams (Ex-Goldman Sachs)

COMPANY METRICS:
- Employees: 500+ globally
- Annual Revenue: $500 million (Series C)

MISSION STATEMENT:
Our mission is to democratize artificial intelligence and make intelligent
systems accessible to every organization, regardless of size or technical expertise.

CORE VALUES:
1. Innovation First - Push boundaries of what's possible
2. Customer Success - Our customers' success is our success
3. Ethical AI - Develop responsible and transparent AI systems
4. Continuous Learning - Never stop growing and improving
""")

w('backend/data/workspaces/default/hr_policies.txt', """
HUMAN RESOURCES POLICIES 2026
==============================

REMOTE WORK POLICY:
- Hybrid Model: 3 days remote, 2 days in-office per week
- Core Hours: 10:00 AM - 4:00 PM local time
- Flexible Start: Begin work between 7 AM - 10 AM
- Home Office Stipend: $150/month for internet

LEAVE POLICY:
- PTO (New employees): 15 days per year
- PTO (3-5 years): 20 days per year
- PTO (5+ years): 25 days per year
- Sick Leave: 10 days per year
- Holidays: 10 company holidays + 2 floating holidays

BENEFITS:
- Health Insurance: 100% premium covered for employee
- Dental & Vision: 75% premium covered
- 401(k) Match: 4% of salary
- Learning Budget: $250/month reimbursement
""")

w('backend/data/workspaces/default/project_phoenix.txt', """
PROJECT PHOENIX - CONFIDENTIAL
================================

CLASSIFICATION: TOP SECRET - INTERNAL ONLY

PROJECT IDENTIFICATION:
- Project Name: Phoenix
- Project Code: OMEGA-PROTOCOL-7
- Status: Active Development
- Priority: Critical

SECRET ACCESS CODE: OMEGA-PROTOCOL-7

KEY DETAILS:
- Launch Date: March 15, 2026
- Total Budget: $10 million
- Project Lead: Dr. Emily Zhang
- Team Size: 25 engineers
- Timeline: 18 months

MILESTONES:
[Completed] Phase 1 - Foundation
[Current] Phase 2 - Development
[Upcoming] Phase 3 - Launch

KEY FEATURES:
1. Real-time data streaming and processing
2. Sub-second query response times
3. Automatic document indexing
4. Multi-modal AI support
5. Enterprise-grade security (SOC2, GDPR)
""")

w('backend/data/workspaces/default/product_roadmap.txt', """
PRODUCT ROADMAP 2026
=====================

Q1 2026 - FOUNDATION:
- January: Release PathwayRAG v2.0
- February: Beta testing with 50 customers
- March: Project Phoenix public launch

Q2 2026 - EXPANSION:
- April: Mobile SDK release (iOS & Android)
- May: European data centers launch
- June: AI Agent framework release

PRICING TIERS:
- Starter: $49/month (up to 5 users)
- Pro: $199/month (up to 25 users)
- Enterprise: Custom pricing (unlimited)

CONTACT:
- Product: product@techventure.com
- Sales: sales@techventure.com
- Support: support@techventure.com
""")

# ── FRONTEND FILES ──────────────────────────────────────────

w('frontend/package.json', """
{
  "name": "livedocs-ai-frontend",
  "private": true,
  "version": "2.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.468.0",
    "react-markdown": "^9.0.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "typescript": "~5.6.2",
    "vite": "^6.0.3"
  }
}
""")

w('frontend/vite.config.ts', """
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/mcp': 'http://localhost:8000',
    },
  },
})
""")

w('frontend/tsconfig.json', """
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"]
}
""")

w('frontend/tailwind.config.js', """
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f5f3ff', 100: '#ede9fe', 200: '#ddd6fe', 300: '#c4b5fd',
          400: '#a78bfa', 500: '#8b5cf6', 600: '#7c3aed', 700: '#6d28d9',
          800: '#5b21b6', 900: '#4c1d95',
        },
      },
    },
  },
  plugins: [],
}
""")

w('frontend/postcss.config.js', """
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}
""")

w('frontend/index.html', """<!DOCTYPE html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚡</text></svg>" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>LiveDocs AI</title>
  </head>
  <body class="bg-slate-950 text-white">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""")

w('frontend/src/index.css', """
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * { @apply border-slate-800; }
  body { @apply bg-slate-950 text-slate-100 antialiased; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
}

@layer components {
  .glass-card { @apply bg-slate-900/60 backdrop-blur-xl border border-slate-800/60 rounded-2xl; }
  .glow-border { @apply border border-brand-500/30 shadow-lg shadow-brand-500/10; }
  .btn-primary { @apply bg-brand-600 hover:bg-brand-500 text-white font-medium px-5 py-2.5 rounded-xl transition-all duration-200 hover:shadow-lg hover:shadow-brand-500/25 active:scale-[0.98]; }
  .btn-ghost { @apply text-slate-400 hover:text-white hover:bg-slate-800 font-medium px-4 py-2 rounded-xl transition-all duration-200; }
  .input-dark { @apply bg-slate-900 border border-slate-700 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 outline-none transition-all duration-200; }
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { @apply bg-slate-700 rounded-full; }
""")

w('frontend/src/main.tsx', """
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><App /></React.StrictMode>,
)
""")

w('frontend/src/types/index.ts', """
export interface Citation { source_file: string; chunk_text: string; relevance_score: number; chunk_index: number; }
export interface AgentStep { agent: string; action: string; thought: string; result: string; latency_ms: number; timestamp: string; }
export interface QueryResponse { answer: string; citations: Citation[]; agent_trace: AgentStep[]; complexity: string; total_latency_ms: number; documents_searched: number; chunks_retrieved: number; model_used: string; conversation_id: string; confidence_score: number; }
export interface DocumentMeta { filename: string; size_bytes: number; modified_at: string; chunk_count: number; doc_type: string; }
export interface DocumentListResponse { documents: DocumentMeta[]; total: number; workspace: string; }
export interface MCPToolManifest { server: { name: string; version: string }; tools: MCPTool[]; tool_count: number; }
export interface MCPTool { name: string; description: string; inputSchema: { type: string; properties: Record<string, { type: string; description: string; required?: boolean }>; required: string[]; }; }
export interface Stats { total_chunks: number; total_documents: number; documents: string[]; bm25_indexed: boolean; }
""")

w('frontend/src/lib/api.ts', """
import type { QueryResponse, DocumentListResponse, Stats, MCPToolManifest } from '../types';
const BASE = '/api/v1';
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!res.ok) throw new Error(await res.text() || 'HTTP ' + res.status);
  return res.json();
}
export const api = {
  query: (question: string, workspace: string, conversationId?: string): Promise<QueryResponse> =>
    request('/query', { method: 'POST', body: JSON.stringify({ question, workspace, conversation_id: conversationId || undefined, agent_mode: true }) }),
  listDocuments: (workspace: string): Promise<DocumentListResponse> => request('/documents?workspace=' + workspace),
  addDocument: (filename: string, content: string, workspace: string) =>
    request('/documents', { method: 'POST', body: JSON.stringify({ filename, content, workspace }) }),
  deleteDocument: (filename: string, workspace: string) =>
    request('/documents/' + filename + '?workspace=' + workspace, { method: 'DELETE' }),
  getStats: (workspace: string): Promise<Stats> => request('/analytics/stats?workspace=' + workspace),
  getMCPManifest: (): Promise<MCPToolManifest> => request('/mcp/manifest'),
};
""")

w('frontend/src/App.tsx', """
import { useState, useRef, useEffect } from 'react';
import { Zap, MessageSquare, FileText, Plug, BarChart3, Send, Trash2, Plus, RefreshCw, ChevronDown, ChevronRight, Bot, Search, Brain, PenTool, Shield, Clock, FileCode, Sparkles, Layers, Activity } from 'lucide-react';
import { api } from './lib/api';
import type { QueryResponse, AgentStep, Citation, Stats, MCPToolManifest } from './types';
import ReactMarkdown from 'react-markdown';

type Tab = 'chat' | 'docs' | 'mcp' | 'stats';
const AGENT_ICONS: Record<string, React.ReactNode> = { orchestrator: <Zap size={14}/>, researcher: <Search size={14}/>, analyst: <Brain size={14}/>, synthesizer: <PenTool size={14}/>, verifier: <Shield size={14}/> };
const AGENT_COLORS: Record<string, string> = { orchestrator: 'text-amber-400 bg-amber-400/10 border-amber-400/30', researcher: 'text-blue-400 bg-blue-400/10 border-blue-400/30', analyst: 'text-purple-400 bg-purple-400/10 border-purple-400/30', synthesizer: 'text-green-400 bg-green-400/10 border-green-400/30', verifier: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30' };

export default function App() {
  const [tab, setTab] = useState<Tab>('chat');
  const [workspace, setWorkspace] = useState('default');
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800/60 bg-slate-900/40 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center shadow-lg shadow-brand-500/25"><Zap size={18} className="text-white"/></div>
            <div><h1 className="text-lg font-bold tracking-tight">LiveDocs AI</h1><p className="text-[11px] text-slate-500 -mt-0.5">Agentic Knowledge Intelligence</p></div>
          </div>
          <div className="flex items-center gap-2">
            <input className="input-dark text-xs w-36" placeholder="Workspace" value={workspace} onChange={e => setWorkspace(e.target.value)}/>
            <span className="text-[10px] text-slate-600 bg-slate-800 px-2 py-1 rounded-lg">v2.0</span>
          </div>
        </div>
      </header>
      <nav className="border-b border-slate-800/40 bg-slate-900/20">
        <div className="max-w-7xl mx-auto px-6 flex gap-1">
          {([['chat','Agentic Query',<MessageSquare size={15}/>],['docs','Documents',<FileText size={15}/>],['mcp','MCP Tools',<Plug size={15}/>],['stats','Analytics',<BarChart3 size={15}/>]] as const).map(([id,label,icon])=>(
            <button key={id} onClick={()=>setTab(id as Tab)} className={"flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 " + (tab===id?"text-brand-400 border-brand-500":"text-slate-500 border-transparent hover:text-slate-300 hover:border-slate-700")}>{icon}{label}</button>
          ))}
        </div>
      </nav>
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-6">
        {tab==='chat'&&<ChatTab workspace={workspace}/>}
        {tab==='docs'&&<DocsTab workspace={workspace}/>}
        {tab==='mcp'&&<MCPTab/>}
        {tab==='stats'&&<StatsTab workspace={workspace}/>}
      </main>
      <footer className="border-t border-slate-800/40 py-3 text-center text-xs text-slate-600">LiveDocs AI v2 - Multi-Agent RAG - MCP Server - Real-Time Intelligence - Team Data Clusters</footer>
    </div>
  );
}

function ChatTab({workspace}:{workspace:string}) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse|null>(null);
  const [convId, setConvId] = useState('');
  const [traceOpen, setTraceOpen] = useState(true);
  const [citationsOpen, setCitationsOpen] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);
  const ask = async () => {
    if (!question.trim()||loading) return;
    setLoading(true);
    try {
      const res = await api.query(question, workspace, convId||undefined);
      setResponse(res); setConvId(res.conversation_id); setQuestion('');
    } catch(err:any) { setResponse({answer:'Error: '+err.message,citations:[],agent_trace:[],complexity:'simple',total_latency_ms:0,documents_searched:0,chunks_retrieved:0,model_used:'',conversation_id:convId,confidence_score:0} as QueryResponse); }
    setLoading(false); inputRef.current?.focus();
  };
  const examples = ['What is the secret code?','Who is the CEO and what is their background?','Compare remote work policy with benefits','Analyze the product roadmap for risks','What are the project milestones?','What is the total budget across projects?'];
  return (<div className="space-y-6">
    <div className="glass-card glow-border p-4">
      <div className="flex gap-3">
        <input ref={inputRef} className="input-dark flex-1 text-sm" placeholder="Ask anything about your documents..." value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>e.key==='Enter'&&ask()} disabled={loading}/>
        <button onClick={ask} disabled={loading||!question.trim()} className="btn-primary flex items-center gap-2 disabled:opacity-40">{loading?<><RefreshCw size={16} className="animate-spin"/>Thinking...</>:<><Send size={16}/>Ask</>}</button>
      </div>
      {!response&&<div className="mt-3 flex flex-wrap gap-2">{examples.map(ex=><button key={ex} onClick={()=>setQuestion(ex)} className="text-xs text-slate-400 bg-slate-800/80 hover:bg-slate-700 px-3 py-1.5 rounded-lg transition-colors">{ex}</button>)}</div>}
    </div>
    {response&&<div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <MetricBadge icon={<Layers size={12}/>} label="Complexity" value={response.complexity}/>
        <MetricBadge icon={<Activity size={12}/>} label="Confidence" value={(response.confidence_score*100).toFixed(0)+'%'}/>
        <MetricBadge icon={<Clock size={12}/>} label="Latency" value={response.total_latency_ms.toFixed(0)+'ms'}/>
        <MetricBadge icon={<FileText size={12}/>} label="Docs" value={String(response.documents_searched)}/>
        <MetricBadge icon={<FileCode size={12}/>} label="Chunks" value={String(response.chunks_retrieved)}/>
        <MetricBadge icon={<Bot size={12}/>} label="Model" value={response.model_used.split('/').pop()||''}/>
      </div>
      <div className="glass-card p-6"><div className="flex items-center gap-2 mb-3"><Sparkles size={16} className="text-brand-400"/><span className="text-sm font-semibold text-brand-400">Answer</span></div><div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed"><ReactMarkdown>{response.answer}</ReactMarkdown></div></div>
      {response.citations.length>0&&<div className="glass-card p-4"><button onClick={()=>setCitationsOpen(!citationsOpen)} className="flex items-center gap-2 text-sm font-semibold text-blue-400 hover:text-blue-300 transition-colors">{citationsOpen?<ChevronDown size={16}/>:<ChevronRight size={16}/>}Citations ({response.citations.length})</button>{citationsOpen&&<div className="mt-3 space-y-2">{response.citations.map((c:Citation,i:number)=><div key={i} className="bg-slate-800/50 rounded-xl p-3 border border-slate-700/40"><div className="flex items-center justify-between mb-1"><span className="text-xs font-medium text-blue-300 flex items-center gap-1.5"><FileText size={12}/>{c.source_file}</span><span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full">Score: {c.relevance_score.toFixed(4)}</span></div><p className="text-xs text-slate-400 line-clamp-2">{c.chunk_text}</p></div>)}</div>}</div>}
      {response.agent_trace.length>0&&<div className="glass-card p-4"><button onClick={()=>setTraceOpen(!traceOpen)} className="flex items-center gap-2 text-sm font-semibold text-purple-400 hover:text-purple-300 transition-colors">{traceOpen?<ChevronDown size={16}/>:<ChevronRight size={16}/>}Agent Pipeline ({response.agent_trace.length} steps)</button>{traceOpen&&<div className="mt-3 space-y-2">{response.agent_trace.map((step:AgentStep,i:number)=><div key={i} className={"rounded-xl p-3 border "+(AGENT_COLORS[step.agent]||'text-slate-400 bg-slate-800 border-slate-700')}><div className="flex items-center justify-between mb-1"><span className="text-xs font-bold flex items-center gap-1.5 uppercase">{AGENT_ICONS[step.agent]}{step.agent}<span className="font-normal text-slate-500">- {step.action}</span></span><span className="text-[10px] opacity-60">{step.latency_ms.toFixed(0)}ms</span></div><p className="text-[11px] opacity-70 mb-0.5">Thought: {step.thought}</p><p className="text-[11px] opacity-80">Result: {step.result}</p></div>)}</div>}</div>}
    </div>}
  </div>);
}

function MetricBadge({icon,label,value}:{icon:React.ReactNode;label:string;value:string}){
  return <div className="flex items-center gap-1.5 bg-slate-800/60 border border-slate-700/40 rounded-lg px-2.5 py-1"><span className="text-slate-500">{icon}</span><span className="text-[10px] text-slate-500">{label}</span><span className="text-xs font-semibold text-slate-300">{value}</span></div>;
}

function DocsTab({workspace}:{workspace:string}) {
  const [docs,setDocs]=useState<any[]>([]);
  const [newName,setNewName]=useState('');
  const [newContent,setNewContent]=useState('');
  const [delName,setDelName]=useState('');
  const [msg,setMsg]=useState('');
  const refresh=async()=>{try{const res=await api.listDocuments(workspace);setDocs(res.documents)}catch{setDocs([])}};
  useEffect(()=>{refresh()},[workspace]);
  const add=async()=>{if(!newName||!newContent)return;try{await api.addDocument(newName,newContent,workspace);setMsg('Added & indexed: '+newName);setNewName('');setNewContent('');refresh()}catch(err:any){setMsg('Error: '+err.message)}};
  const del=async()=>{if(!delName)return;try{await api.deleteDocument(delName,workspace);setMsg('Deleted: '+delName);setDelName('');refresh()}catch(err:any){setMsg('Error: '+err.message)}};
  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><h2 className="text-lg font-bold">Knowledge Base</h2><button onClick={refresh} className="btn-ghost flex items-center gap-2 text-xs"><RefreshCw size={14}/>Refresh</button></div>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">{docs.map(d=><div key={d.filename} className="glass-card p-4 hover:border-brand-500/30 transition-colors"><div className="flex items-center gap-2 mb-2"><FileText size={16} className="text-brand-400"/><span className="text-sm font-medium truncate">{d.filename}</span></div><div className="text-xs text-slate-500 space-y-1"><p>Size: {(d.size_bytes/1024).toFixed(1)} KB</p><p>Type: {d.doc_type}</p></div></div>)}{docs.length===0&&<div className="col-span-full text-center py-12 text-slate-600"><FileText size={40} className="mx-auto mb-3 opacity-30"/><p>No documents found.</p></div>}</div>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="glass-card p-4"><h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><Plus size={14} className="text-green-400"/>Add Document</h3><input className="input-dark w-full text-sm mb-2" placeholder="filename.txt" value={newName} onChange={e=>setNewName(e.target.value)}/><textarea className="input-dark w-full text-sm mb-3 min-h-[80px] resize-y" placeholder="Content..." value={newContent} onChange={e=>setNewContent(e.target.value)}/><button onClick={add} className="btn-primary text-sm w-full">Add & Index</button></div>
      <div className="glass-card p-4"><h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><Trash2 size={14} className="text-red-400"/>Delete Document</h3><input className="input-dark w-full text-sm mb-3" placeholder="filename.txt" value={delName} onChange={e=>setDelName(e.target.value)}/><button onClick={del} className="w-full text-sm bg-red-600/80 hover:bg-red-500 text-white font-medium px-5 py-2.5 rounded-xl transition-all duration-200">Delete</button></div>
    </div>
    {msg&&<p className="text-sm text-center text-slate-400 glass-card p-3">{msg}</p>}
  </div>);
}

function MCPTab() {
  const [manifest,setManifest]=useState<MCPToolManifest|null>(null);
  useEffect(()=>{api.getMCPManifest().then(setManifest).catch(()=>setManifest(null))},[]);
  return (<div className="space-y-6">
    <div><h2 className="text-lg font-bold">Model Context Protocol</h2><p className="text-sm text-slate-500 mt-1">MCP allows AI models (Claude, Cursor, etc.) to discover and call LiveDocs tools.</p></div>
    <div className="glass-card p-4"><h3 className="text-sm font-semibold mb-3 text-brand-400">Connect Claude Desktop</h3><pre className="bg-slate-950 rounded-xl p-4 text-xs text-slate-300 overflow-x-auto">{JSON.stringify({mcpServers:{livedocs:{url:"http://localhost:8000/mcp"}}},null,2)}</pre><p className="text-xs text-slate-500 mt-2">Add to claude_desktop_config.json</p></div>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">{manifest?.tools.map(tool=><div key={tool.name} className="glass-card p-4 hover:border-brand-500/30 transition-colors"><div className="flex items-center gap-2 mb-2"><div className="w-7 h-7 rounded-lg bg-brand-600/20 flex items-center justify-center"><Plug size={14} className="text-brand-400"/></div><code className="text-sm font-bold text-brand-300">{tool.name}</code></div><p className="text-xs text-slate-400 mb-3">{tool.description}</p><div className="space-y-1">{Object.entries(tool.inputSchema.properties).map(([name,param]:[string,any])=><div key={name} className="flex items-center gap-2 text-[11px]"><code className="text-purple-300">{name}</code><span className="text-slate-600">{param.type}</span>{tool.inputSchema.required.includes(name)&&<span className="text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded text-[9px]">required</span>}</div>)}</div></div>)}</div>
    <div className="glass-card p-4"><h3 className="text-sm font-semibold mb-3 text-green-400">REST API</h3><pre className="bg-slate-950 rounded-xl p-4 text-xs text-slate-300 overflow-x-auto">{"curl http://localhost:8000/api/v1/mcp/manifest\\n\\ncurl -X POST http://localhost:8000/api/v1/mcp/call\\n  -H 'Content-Type: application/json'\\n  -d '{\"tool_name\":\"search_documents\",\"arguments\":{\"query\":\"secret code\"}}'"}</pre></div>
  </div>);
}

function StatsTab({workspace}:{workspace:string}) {
  const [stats,setStats]=useState<Stats|null>(null);
  const load=async()=>{try{setStats(await api.getStats(workspace))}catch{setStats(null)}};
  useEffect(()=>{load()},[workspace]);
  return (<div className="space-y-6">
    <div className="flex items-center justify-between"><h2 className="text-lg font-bold">Analytics</h2><button onClick={load} className="btn-ghost flex items-center gap-2 text-xs"><RefreshCw size={14}/>Refresh</button></div>
    {stats&&<div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div className="glass-card p-4 text-center"><div className="text-blue-400 flex justify-center mb-2"><FileText size={20}/></div><p className="text-xl font-bold">{stats.total_documents}</p><p className="text-xs text-slate-500">Documents</p></div>
      <div className="glass-card p-4 text-center"><div className="text-purple-400 flex justify-center mb-2"><Layers size={20}/></div><p className="text-xl font-bold">{stats.total_chunks}</p><p className="text-xs text-slate-500">Chunks</p></div>
      <div className="glass-card p-4 text-center"><div className="text-green-400 flex justify-center mb-2"><Search size={20}/></div><p className="text-xl font-bold">{stats.bm25_indexed?'Active':'Inactive'}</p><p className="text-xs text-slate-500">BM25 Index</p></div>
      <div className="glass-card p-4 text-center"><div className="text-amber-400 flex justify-center mb-2"><Bot size={20}/></div><p className="text-xl font-bold">{workspace}</p><p className="text-xs text-slate-500">Workspace</p></div>
    </div>}
    {stats&&stats.documents.length>0&&<div className="glass-card p-4"><h3 className="text-sm font-semibold mb-3">Indexed Files</h3><div className="space-y-2">{stats.documents.map(f=><div key={f} className="flex items-center gap-2 text-sm text-slate-400 bg-slate-800/40 rounded-lg px-3 py-2"><FileText size={14} className="text-brand-400"/><span>{f}</span></div>)}</div></div>}
    <div className="glass-card p-4"><h3 className="text-sm font-semibold mb-3 text-brand-400">Pipeline Architecture</h3><pre className="bg-slate-950 rounded-xl p-4 text-xs text-slate-400 overflow-x-auto">{"Query -> Orchestrator -> Research -> Analyze -> Synthesize -> Verify\\n                           |\\n                     RAG Engine\\n                 +------|------+\\n             ChromaDB        BM25\\n             (Dense)       (Sparse)\\n                 +------|------+\\n                  RRF Fusion -> LLM Reranker\\n                              |\\n                  MCP Server (6 Tools)\\n                              |\\n                  File Watcher (Real-Time)"}</pre></div>
  </div>);
}
""")

w('frontend/Dockerfile', """
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY <<'NGINX' /etc/nginx/conf.d/default.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
    }
    location /mcp {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
    }
}
NGINX
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
""")

print()
print('=' * 60)
print('  All files created successfully!')
print('=' * 60)
print()
print('NEXT STEPS:')
print()
print('  1. Edit .env - add your OpenRouter API key')
print('  2. cd backend')
print('  3. python -m venv .venv')
print('  4. .venv\\Scripts\\activate')
print('  5. pip install -r requirements.txt')
print('  6. python run.py')
print()
print('  Frontend (separate terminal):')
print('  7. cd frontend')
print('  8. npm install')
print('  9. npm run dev')
print()
print('  Then open http://localhost:5173')
print()
