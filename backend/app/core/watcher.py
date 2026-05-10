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
