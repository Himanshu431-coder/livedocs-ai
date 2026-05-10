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
