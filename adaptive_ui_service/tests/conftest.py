from pathlib import Path

import pytest

from adaptive_ui_service.app.core.config import settings


@pytest.fixture(autouse=True)
def use_missing_retrieval_index(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "index_dir", tmp_path / "missing-index")
