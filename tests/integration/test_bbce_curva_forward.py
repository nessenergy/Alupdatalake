"""Chamada real à API do BBCE Connect.

Pulado enquanto a Alup não entrega o acesso somente leitura (pendência A7,
issue #23). Para rodar quando a credencial existir no Secret Manager:

    ALUPDATA_INTEGRACAO_BBCE=1 uv run pytest tests/integration -q

O que este teste responde, e que a coleção Postman não permite afirmar:

1. **qual é o host.** A coleção usa `{{baseUrl}}` sem valor; o endereço vem com
   o acesso. Sem ele o conector nem chega a tentar;
2. o `Authorization` espera o JWT cru ou prefixado com `Bearer`? A coleção usa
   a variável `{{jwt}}`, que não revela o formato;
3. dia sem pregão devolve lista vazia, 404 ou erro?
4. a curva traz mais de um `name` (produto), ou só `PLD`?
5. o `vertexDate` continua vindo como meia-noite de Brasília em UTC?
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import pytest
from src.conectores.bbce_curva_forward import BbceCurvaForward, VerticeCurva
from src.core.execucao import Janela

pytestmark = pytest.mark.skipif(
    not os.getenv("ALUPDATA_INTEGRACAO_BBCE"),
    reason="acesso ao BBCE ainda não entregue (pendência A7, issue #23)",
)


def test_autentica_e_obtem_token() -> None:
    assert BbceCurvaForward()._token()


def test_curva_de_um_dia_util_recente() -> None:
    conector = BbceCurvaForward()

    # Volta até achar um pregão: fim de semana e feriado não têm curva.
    dia = date.today() - timedelta(days=1)
    for _ in range(10):
        if vertices := conector._curva_do_dia(dia):
            assert all("vertexDate" in v and "vertexValue" in v for v in vertices)
            return
        dia -= timedelta(days=1)

    pytest.fail("nenhuma curva encontrada em 10 dias — o contrato de dados mudou?")


def test_extrai_e_valida_janela_curta() -> None:
    conector = BbceCurvaForward()

    for bruto in conector.extrair(Janela.ultimos_dias(7)):
        VerticeCurva.model_validate(conector.transformar(bruto))
