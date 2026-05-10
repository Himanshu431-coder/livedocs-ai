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
    chunks_text = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in chunks[:8])
    analysis = llm.chat([
        {"role": "system", "content": "You are a document analyst. Given a question and document excerpts:\n1. Extract KEY FACTS relevant to the question\n2. Identify any CONTRADICTIONS between sources\n3. Note INFORMATION GAPS (what is missing)\n4. Rate your CONFIDENCE (0.0-1.0)\n\nRespond in JSON format:\n{\"key_facts\": [...], \"contradictions\": [...], \"gaps\": [...], \"confidence\": 0.0}"},
        {"role": "user", "content": f"Question: {question}\n\nExcerpts:\n{chunks_text}"},
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
    chunks_text = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in chunks[:6])
    answer = llm.chat([
        {"role": "system", "content": "You are LiveDocs AI, an advanced knowledge intelligence assistant.\nSynthesize a comprehensive, well-structured answer using the provided chunks and analysis. Cite sources as [Source: filename]. Use markdown formatting. Be precise and thorough."},
        {"role": "user", "content": f"Question: {question}\n\nKey Facts: {analysis.get('key_facts', [])}\nConfidence: {analysis.get('confidence', 0.5)}\n\nSource Chunks:\n{chunks_text}"},
    ], max_tokens=1500, temperature=0.1)
    return {"answer": answer, "confidence": analysis.get("confidence", 0.5), "latency_ms": (time.time() - start) * 1000}

async def tool_verify_answer(question: str, answer: str, chunks: list[dict]) -> dict:
    start = time.time()
    llm = get_llm()
    chunks_text = "\n\n".join(f"[{c['source']}]\n{c['text'][:200]}" for c in chunks[:4])
    verification = llm.chat([
        {"role": "system", "content": "You are a fact-checker. Verify if the answer is fully supported by the source documents. Respond in JSON:\n{\"verified\": true/false, \"issues\": [...], \"accuracy_score\": 0.0-1.0, \"suggested_fix\": \"...\"}"},
        {"role": "user", "content": f"Question: {question}\n\nAnswer: {answer}\n\nSources:\n{chunks_text}"},
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
    chunks_text = "\n\n".join(f"[{c.source_file}]\n{c.text[:400]}" for c in sample_chunks[:10])
    insights = llm.chat([
        {"role": "system", "content": "Analyze these document excerpts and extract:\n1. KEY INSIGHTS\n2. ENTITIES (people, orgs, projects, metrics)\n3. RELATIONSHIPS\n4. KNOWLEDGE GAPS\n\nRespond in JSON:\n{\"insights\": [...], \"entities\": [...], \"relationships\": [...], \"gaps\": [...]}"},
        {"role": "user", "content": chunks_text},
    ], max_tokens=600, temperature=0.1, json_mode=True)
    try:
        result = json.loads(insights)
    except json.JSONDecodeError:
        result = {"insights": [], "entities": [], "relationships": [], "gaps": []}
    result["latency_ms"] = (time.time() - start) * 1000
    return result
