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
