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
    # A marca de início da ingestão fala com o BigQuery quando `dry_run` está desligado, e vários testes do
    # runner o desligam para exercitar o caminho completo. Sem isto, onde há `gcloud` instalado o cliente
    # real tenta autenticar e o teste trava; onde não há, falha engolida. O teste da marca a restaura.
    monkeypatch.setattr("src.core.conector.registrar_inicio", lambda _execucao: None)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
