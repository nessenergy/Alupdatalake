"""Leitura real do MySQL Alup (Onda 3): confere o contrato de colunas contra o banco, sem gravar nada.

Pulado sem credencial. Para rodar, grave a DSN no cofre local (`ALUPDATA_SECRETS_LOCAIS=1`) ou use o Secret Manager, com
a rede de dev (ADR 024), e exporte `ALUPDATA_INTEGRACAO_PORTAL_ALUP=1`. Cada conector lê uma janela de um dia e o
modelo Pydantic valida as linhas: tipo ou anulabilidade que o dicionário errou aparece aqui na primeira carga.
"""

from __future__ import annotations

import os

import pytest
from src.conectores.mysql_alup import (
    PortalAlupBandeira,
    PortalAlupClient,
    PortalAlupFaturasProcessadas,
    PortalAlupInvoice,
    PortalAlupUc,
)
from src.core.execucao import Janela

pytestmark = pytest.mark.skipif(
    not os.getenv("ALUPDATA_INTEGRACAO_PORTAL_ALUP"),
    reason="requer a DSN do MySQL Alup (secret alupdata-portal-alup-dsn) e a rede de dev",
)

JANELA = Janela.de_texto("2026-11-01", "2026-11-01")


@pytest.mark.parametrize(
    "conector",
    [PortalAlupClient, PortalAlupUc, PortalAlupBandeira, PortalAlupInvoice, PortalAlupFaturasProcessadas],
)
def test_as_colunas_do_dicionario_existem_e_as_linhas_validam(conector):
    instancia = conector()
    linhas = []
    for bruto in instancia.extrair(JANELA):
        linhas.append(conector.schema.model_validate(instancia.transformar(bruto)))
        if len(linhas) == 50:  # amostra: o objetivo é o contrato de colunas, não o volume
            break

    # Tabela vazia na janela é resultado válido para os fatos; o SELECT já provou que as colunas existem.
    assert all(linha.id is not None for linha in linhas)
