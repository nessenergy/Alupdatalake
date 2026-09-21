"""Chamada real ao endpoint de download do TempoOK — produto ENA-PREVS.

Pulado sem opt-in explícito. Para rodar, com o token no cofre local ou no
Secret Manager (nunca em variável de ambiente do repositório):

    ALUPDATA_INTEGRACAO_TEMPOOK=1 ALUPDATA_SECRETS_LOCAIS=1 uv run pytest tests/integration -q

Diferente do boletim, aqui a origem **responde para datas atuais** — é por isso
que estes testes existem: se pararem de responder, o produto mudou de lugar.
Verificado em 21/09/2026: 43 de 45 dias, ~94 KB por arquivo, TLS sem ajuste.
"""

from __future__ import annotations

import datetime
import os

import pytest
from src.conectores.tempook_ena_prevs import ArquivoEnaPrevs, TempookEnaPrevs, caminho_do_dia
from src.core.execucao import Janela

pytestmark = pytest.mark.skipif(
    not os.getenv("ALUPDATA_INTEGRACAO_TEMPOOK"),
    reason="opt-in explícito: chama a origem real com o token do TempoOK",
)


def test_o_exemplo_da_alup_ainda_responde() -> None:
    """2026-09-15 é o caminho que a Alup entregou em 18/09."""
    conteudo = TempookEnaPrevs()._baixar(caminho_do_dia(datetime.date(2026, 9, 15)))

    assert conteudo is not None, "o caminho do exemplo deixou de responder — o produto mudou de lugar?"
    assert conteudo.startswith(b"\x1f\x8b")


def test_tls_passa_sem_desligar_a_verificacao() -> None:
    """O exemplo da Alup usa verify=False; a ADR 019 recusa isso. Se este teste
    falhar com erro de certificado, o caminho é acionar o TempoOK — não desligar
    a verificação."""
    TempookEnaPrevs()._baixar(caminho_do_dia(datetime.date(2026, 9, 15)))  # não deve levantar SSLError


def test_extrai_e_valida_janela_recente() -> None:
    conector = TempookEnaPrevs()

    registros = list(conector.extrair(Janela.ultimos_dias(7)))

    assert registros, "nenhum arquivo nos últimos 7 dias: a série parou?"
    for bruto in registros:
        ArquivoEnaPrevs.model_validate(conector.transformar(bruto))
