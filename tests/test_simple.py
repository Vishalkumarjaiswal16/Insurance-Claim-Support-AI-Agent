from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from customer_support_agent.api.app_factory import create_app
from customer_support_agent.core.settings import Settings
from customer_support_agent.repositories.sqlite import base as sqlite_base


def test_health_endpoint_returns_ok(tmp_path: Path, monkeypatch) -> None:
    settings = Settings(
        workspace_dir=tmp_path,
        data_dir=Path("data"),
        db_path=Path("data/support.db"),
        chroma_rag_dir=Path("data/chroma_rag"),
        chroma_mem0_dir=Path("data/chroma_mem0"),
        knowledge_base_dir=Path("knowledge_base"),
        _env_file=None,
    )

    monkeypatch.setattr(sqlite_base, "get_settings", lambda: settings)
    monkeypatch.setattr(sqlite_base, "_DB_INITIALIZED", False)

    app = create_app(settings=settings)
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
