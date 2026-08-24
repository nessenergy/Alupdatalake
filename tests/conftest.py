"""Fixtures compartilhadas para testes do AlupData."""

import pytest


@pytest.fixture
def sample_config():
    """Retorna configuração de teste."""
    return {
        "project_id": "alupdata-test",
        "dataset_bronze": "test_bronze",
        "dataset_silver": "test_silver",
        "dataset_gold": "test_gold",
    }
