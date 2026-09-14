"""Chamada real ao endpoint de download do TempoOK.

Pulado enquanto a Alup não entrega o token no Secret Manager (pendência A7).
Para rodar quando a credencial existir:

    ALUPDATA_INTEGRACAO_TEMPOOK=1 uv run pytest tests/integration -q

Este é o teste que responde o que o exemplo de um único dia não permite
afirmar, e que está listado como não verificado no dicionário de dados:

1. o template do caminho vale para toda data, ou só para o exemplo de 2022-03?
2. como a origem sinaliza um dia sem boletim — 404, corpo vazio ou HTML?
3. a verificação de TLS passa sem `verify=False`?
4. o PDF de um dia é estável, ou a origem republica com bytes diferentes?
"""

from __future__ import annotations

import os

import pytest
from src.conectores.tempook_boletins import Boletim, TempookBoletins, caminho_do_dia
from src.core.execucao import Janela

pytestmark = pytest.mark.skipif(
    not os.getenv("ALUPDATA_INTEGRACAO_TEMPOOK"),
    reason="token do TempoOK ainda não entregue no Secret Manager (pendência A7)",
)


def test_o_exemplo_conhecido_ainda_responde() -> None:
    """2022-03-31 é o único caminho que se sabe existir: veio no e-mail de 14/09."""
    conector = TempookBoletins()

    conteudo = conector._baixar(caminho_do_dia(__import__("datetime").date(2022, 3, 31)))

    assert conteudo is not None, "o caminho do exemplo deixou de responder — o template mudou?"
    assert conteudo.startswith(b"%PDF-")


def test_tls_passa_sem_desligar_a_verificacao() -> None:
    """O exemplo fornecido usa verify=False; a ADR 019 recusa isso.

    Se este teste falhar com erro de certificado, o caminho é a Alup acionar o
    TempoOK — não desligar a verificação.
    """
    import datetime

    conector = TempookBoletins()

    conector._baixar(caminho_do_dia(datetime.date(2022, 3, 31)))  # não deve levantar SSLError


def test_extrai_e_valida_janela_curta() -> None:
    conector = TempookBoletins()

    for bruto in conector.extrair(Janela.ultimos_dias(7)):
        Boletim.model_validate(conector.transformar(bruto))
