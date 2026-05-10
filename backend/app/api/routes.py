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
