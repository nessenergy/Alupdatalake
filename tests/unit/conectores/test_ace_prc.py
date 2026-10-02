"""Conector ACE — PRC publicado em alup.io/valores-de-energia (HTML, uma tabela).

A fixture é o HTML real da página em 02/10/2026 (tabela do TablePress com `rowspan` no submercado e o
parágrafo "Atualizado em"). Sem rede.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ace_prc import AcePrc, LayoutInesperadoError
from src.conectores.planilha_prc import PrecoReferencia
from src.core.config import get_settings
from src.core.execucao import Janela

HTML = (Path(__file__).parents[2] / "fixtures" / "ace_prc.html").read_text(encoding="utf-8")
JANELA = Janela.de_texto("2026-09-25", "2026-10-02")


@pytest.fixture(autouse=True)
def _dry_run() -> None:
    get_settings().dry_run = True


def _conector(monkeypatch: pytest.MonkeyPatch, html: str = HTML) -> AcePrc:
    monkeypatch.setattr("src.conectores.ace_prc.criar_sessao", lambda: None)
    conector = AcePrc()
    monkeypatch.setattr(conector, "_baixar", lambda: html)
    return conector


def _registros(conector: AcePrc) -> list[PrecoReferencia]:
    return [PrecoReferencia.model_validate(conector.transformar(b)) for b in conector.extrair(JANELA)]


def test_a_tabela_inteira_vira_24_precos(monkeypatch: pytest.MonkeyPatch) -> None:
    """4 submercados × 2 tipos de energia × 3 prazos."""
    registros = _registros(_conector(monkeypatch))

    assert len(registros) == 24
    assert {(r.submercado, r.tipo_energia, r.prazo_meses) for r in registros} == {
        (s, t, p) for s in ("SE", "S", "NE", "N") for t in ("convencional", "incentivada_50") for p in (12, 36, 60)
    }


@pytest.mark.parametrize(
    ("submercado", "tipo", "prazo", "preco"),
    [
        ("SE", "incentivada_50", 12, "280.00"),  # SE/CO vira a sigla SE da dimensão comum
        ("S", "convencional", 36, "219.00"),
        ("NE", "incentivada_50", 36, "209.67"),
        ("N", "convencional", 60, "181.40"),  # a página escreve "Convecional" nesta linha
    ],
)
def test_valores_conferem_com_a_pagina(monkeypatch, submercado, tipo, prazo, preco) -> None:
    registros = _registros(_conector(monkeypatch))
    [achado] = [r for r in registros if (r.submercado, r.tipo_energia, r.prazo_meses) == (submercado, tipo, prazo)]

    assert achado.preco_rs_mwh == Decimal(preco)


def test_data_de_atualizacao_e_a_que_a_pagina_declara(monkeypatch: pytest.MonkeyPatch) -> None:
    registros = _registros(_conector(monkeypatch))

    assert {r.data_atualizacao for r in registros} == {date(2025, 10, 1)}
    assert {r.comercializadora for r in registros} == {"ACE Comercializadora"}
    assert {r.ano for r in registros} == {None}


def test_a_janela_nao_filtra_o_retrato_da_pagina(monkeypatch: pytest.MonkeyPatch) -> None:
    """A página é um retrato: a data dela (01/10/2025) está fora de qualquer janela recente."""
    conector = _conector(monkeypatch)

    assert len(list(conector.extrair(Janela.de_texto("2026-10-01", "2026-10-02")))) == 24


def test_pagina_sem_tabela_falha_alto_em_vez_de_carregar_zero_linhas(monkeypatch: pytest.MonkeyPatch) -> None:
    conector = _conector(monkeypatch, "<html><body><p>Atualizado em: 01/10/2025.</p></body></html>")

    with pytest.raises(LayoutInesperadoError, match="tabela"):
        list(conector.extrair(JANELA))


def test_pagina_sem_data_de_atualizacao_falha_alto(monkeypatch: pytest.MonkeyPatch) -> None:
    sem_data = HTML.replace("Atualizado em: 01/10/2025.", "")
    conector = _conector(monkeypatch, sem_data)

    with pytest.raises(LayoutInesperadoError, match="Atualizado em"):
        list(conector.extrair(JANELA))


def test_prazo_novo_no_cabecalho_nao_passa_em_silencio(monkeypatch: pytest.MonkeyPatch) -> None:
    html = HTML.replace("(5 anos)", "(7 anos)")
    conector = _conector(monkeypatch, html)

    with pytest.raises(LayoutInesperadoError, match="prazo"):
        list(conector.extrair(JANELA))


def test_tipo_de_energia_desconhecido_vira_linha_invalida(monkeypatch: pytest.MonkeyPatch) -> None:
    conector = _conector(monkeypatch)
    bruto = next(iter(conector.extrair(JANELA))) | {"tipo_energia": "Mágica"}

    with pytest.raises(ValueError, match="tipo de energia"):
        conector.transformar(bruto)


def test_ciclo_completo_no_runner_sem_rede(monkeypatch: pytest.MonkeyPatch) -> None:
    execucao = _conector(monkeypatch).ingerir(JANELA)

    assert (execucao.linhas_extraidas, execucao.linhas_invalidas) == (24, 0)
