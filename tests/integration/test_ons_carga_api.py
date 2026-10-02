"""Chamada real à API de carga do ONS (programada e verificada).

A API é pública (sem token), mas o teste chama a internet: pulado sem opt-in.

    ALUPDATA_INTEGRACAO_ONS=1 uv run pytest tests/integration/test_ons_carga_api.py -q

Verificado em 02/10/2026: duas áreas, três dias, 144 linhas em cada endpoint.
"""

from __future__ import annotations

import os

import pytest
from src.conectores import ons_carga_api
from src.conectores.ons_carga_programada import OnsCargaProgramada
from src.conectores.ons_carga_verificada import OnsCargaVerificada
from src.core.execucao import Janela

pytestmark = pytest.mark.skipif(
    not os.getenv("ALUPDATA_INTEGRACAO_ONS"),
    reason="opt-in explícito: chama a API real do ONS (pública, sem credencial)",
)

JANELA = Janela.de_texto("2026-09-20", "2026-09-22")


@pytest.mark.parametrize("classe", [OnsCargaProgramada, OnsCargaVerificada])
def test_api_responde_e_o_schema_aceita_o_dado_real(classe, monkeypatch) -> None:
    monkeypatch.setattr(ons_carga_api, "AREAS_CARGA", ("N", "SECO"))
    conector = classe()

    registros = [conector.schema.model_validate(conector.transformar(b)) for b in conector.extrair(JANELA)]

    assert len(registros) == 2 * 3 * 48  # 2 áreas, 3 dias, 48 meias horas
    assert {r.area_carga for r in registros} == {"N", "SECO"}
