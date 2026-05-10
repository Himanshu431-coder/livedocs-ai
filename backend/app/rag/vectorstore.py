import chromadb
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
        persist_path = str(self.settings.data_dir / workspace / ".chroma")
        self._client = chromadb.PersistentClient(path=persist_path)
        self._collection = self._client.get_or_create_collection(
            name=f"livedocs_{workspace}",
            metadata={"hnsw:space": "cosine"},
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
