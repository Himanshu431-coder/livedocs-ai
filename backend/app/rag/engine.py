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
            chunks_text += f"\n[CHUNK {i}] (score: {score:.4f})\n{chunk.text[:300]}\n"
        try:
            response = self.llm.chat([
                {"role": "system", "content": "You are a relevance ranking engine. Return only a JSON array of integers."},
                {"role": "user", "content": f'Given the query: "{query}"\n\nRank these chunks by relevance (most relevant first). Return ONLY a JSON array of chunk indices.\n\nChunks:{chunks_text}\nRanked indices:'},
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
            context_parts.append(f"[Source: {chunk.source_file}, Chunk {chunk.chunk_index}, Relevance: {score:.4f}]\n{chunk.text}")
        context = "\n\n---\n\n".join(context_parts)
        system_prompt = "You are LiveDocs AI, an advanced knowledge intelligence assistant.\nRULES:\n1. Answer based ONLY on the provided document chunks.\n2. Cite sources using [Source: filename] format.\n3. If the answer is not in the documents, say: I don't have sufficient information in the current knowledge base to answer this question.\n4. Be precise, structured, and comprehensive.\n5. Use markdown formatting for clarity.\n6. If multiple sources contribute, synthesize them."
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history[-6:])
        messages.append({"role": "user", "content": f"Document Chunks:\n{context}\n\n---\n\nQuestion: {query}\n\nProvide a comprehensive answer with citations:"})
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
