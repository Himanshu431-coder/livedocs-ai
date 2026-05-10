import os
import uvicorn
from app.config import get_settings

def main():
    settings = get_settings()
    port = int(os.environ.get("PORT", settings.port))
    print()
    print("=" * 60)
    print("  LiveDocs AI v2.0")
    print("  Agentic Knowledge Intelligence Platform")
    print("  Agents - MCP - Real-Time")
    print("=" * 60)
    print()
    print(f"  API:  http://{settings.host}:{port}/api/v1")
    print(f"  MCP:  http://{settings.host}:{port}/mcp")
    print(f"  Docs: http://{settings.host}:{port}/docs")
    print()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=port,
        reload=settings.debug,
        log_level="info",
    )

if __name__ == "__main__":
    main()
