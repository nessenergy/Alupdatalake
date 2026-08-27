"""Chamada real à API do Hubspot.

Pulado enquanto a Alup não entrega o token (pendência A5). Para rodar quando a
credencial existir no Secret Manager:

    ALUPDATA_INTEGRACAO_HUBSPOT=1 uv run pytest tests/integration -q
"""

from __future__ import annotations

import os

import pytest
from src.conectores.hubspot_negocios import HubspotNegocios, Negocio
from src.core.execucao import Janela

pytestmark = pytest.mark.skipif(
    not os.getenv("ALUPDATA_INTEGRACAO_HUBSPOT"),
    reason="token do Hubspot ainda não entregue (pendência A5)",
)


def test_extrai_e_valida_janela_curta() -> None:
    conector = HubspotNegocios()
    brutos = list(conector.extrair(Janela.ultimos_dias(7)))
    for bruto in brutos:
        Negocio.model_validate(conector.transformar(bruto))
