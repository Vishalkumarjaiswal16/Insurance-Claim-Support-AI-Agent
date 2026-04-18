from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_project_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return None


def _resolve_workspace_dir() -> Path:
    env_workspace_dir = (
        os.getenv("CUSTOMER_SUPPORT_AGENT_WORKSPACE_DIR") or os.getenv("WORKSPACE_DIR")
    )
    if env_workspace_dir:
        return Path(env_workspace_dir).expanduser().resolve()

    cwd_root = _find_project_root(Path.cwd().resolve())
    if cwd_root is not None:
        return cwd_root

    file_root = _find_project_root(Path(__file__).resolve().parent)
    if file_root is not None:
        return file_root

    return Path.cwd().resolve()


WORKSPACE_DIR = _resolve_workspace_dir()


def _resolve_env_file(workspace_dir: Path) -> Path:
    env_file_override = (
        os.getenv("CUSTOMER_SUPPORT_AGENT_ENV_FILE") or os.getenv("ENV_FILE")
    )
    if env_file_override:
        return Path(env_file_override).expanduser().resolve()
    return workspace_dir / ".env"


ENV_FILE = _resolve_env_file(WORKSPACE_DIR)


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Copilot for Support Agents"

    groq_api_key: SecretStr | None = None
    groq_model: str = "llama-3.1-8b-instant"
    llm_temperature: float = 0.2


    openai_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None
    google_embedding_model: str = "gemini-embedding-001"
    enable_local_embeddings: bool = False

    workspace_dir: Path = WORKSPACE_DIR
    data_dir: Path = Path("data")
    db_path: Path = Path("data/support.db")
    chroma_rag_dir: Path = Path("data/chroma_rag")
    chroma_mem0_dir: Path = Path("data/chroma_mem0")
    knowledge_base_dir: Path = Path("knowledge_base")

    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_top_k: int = 4
    mem0_top_k: int = 5

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    dashboard_api_url: str = ""

    def model_post_init(self, __context) -> None:
        if (self.dashboard_api_url or "").strip():
            return

        dashboard_host = (
            "localhost" if self.api_host in {"0.0.0.0", "::", ""} else self.api_host
        )
        object.__setattr__(
            self, "dashboard_api_url", f"http://{dashboard_host}:{self.api_port}"
        )

    def resolve(self, path: Path) -> Path:
        """Resolve relative paths against the workspace directory."""
        return path if path.is_absolute() else self.workspace_dir / path

    @property
    def db_file(self) -> Path:
        return self.resolve(self.db_path)

    @property
    def chroma_rag_path(self) -> Path:
        return self.resolve(self.chroma_rag_dir)

    @property
    def chroma_mem0_path(self) -> Path:
        return self.resolve(self.chroma_mem0_dir)

    @property
    def knowledge_base_path(self) -> Path:
        return self.resolve(self.knowledge_base_dir)

    @property
    def effective_google_embedding_model(self) -> str:
        """
        Normalize and auto-upgrade legacy embedding model IDs to a supported Gemini model.
        """
        model = (self.google_embedding_model or "").strip()
        if not model:
            return "gemini-embedding-001"

        if model.startswith("models/"):
            model = model[len("models/") :]

        deprecated_aliases = {
            "text-embedding-004",
            "embedding-001",
            "embedding-gecko-001",
            "gemini-embedding-exp",
            "gemini-embedding-exp-03-07",
        }
        if model in deprecated_aliases:
            return "gemini-embedding-001"

        return model

    @staticmethod
    def _reveal_secret(secret: SecretStr | None) -> str:
        return secret.get_secret_value() if secret else ""

    @property
    def groq_api_key_value(self) -> str:
        return self._reveal_secret(self.groq_api_key)

    @property
    def openai_api_key_value(self) -> str:
        return self._reveal_secret(self.openai_api_key)

    @property
    def google_api_key_value(self) -> str:
        return self._reveal_secret(self.google_api_key)

@lru_cache
def get_settings() -> Settings:
    return Settings()


def ensure_directories(settings: Settings | None = None) -> None:
    """Create the local directories required by SQLite and ChromaDB."""
    config = settings or get_settings()

    for path in (
        config.resolve(config.data_dir),
        config.db_file.parent,
        config.chroma_rag_path,
        config.chroma_mem0_path,
        config.knowledge_base_path,
    ):
        path.mkdir(parents=True, exist_ok=True)
