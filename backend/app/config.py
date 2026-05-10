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
