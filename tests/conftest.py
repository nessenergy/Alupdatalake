"""Fixtures compartilhadas.

Teste unitário nunca toca GCP: `dry_run` fica ligado por padrão e a
configuração é relida a cada teste.
"""

import pytest
from src.core.config import get_settings


@pytest.fixture(autouse=True)
def ambiente_de_teste(monkeypatch):
    """Isola a configuração e desliga qualquer gravação em GCS/BigQuery."""
    monkeypatch.setenv("GCP_PROJECT_ID", "alupdata-test")
    monkeypatch.setenv("GCS_BUCKET_RAW", "alupdata-test-raw")
    monkeypatch.setenv("DRY_RUN", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
