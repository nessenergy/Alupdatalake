"""Conector ONS — geração térmica por motivo de despacho: CSV mensal, sem rede.

Fixtures com linhas reais: 09/2026 (47 colunas), 09/2024 (42) e 01/2022 (41). O cabeçalho
cresceu três vezes na série; o conector lê por nome de coluna e deixa NULL o que o mês não tem.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_geracao_termica_despacho import (
    _MEDIDAS,
    GeracaoTermicaDespacho,
    OnsGeracaoTermicaDespacho,
)
from src.core.execucao import Janela

FIXTURES = Path(__file__).parents[2] / "fixtures"
ATUAL = FIXTURES / "ons_geracao_termica_despacho_202609.csv"
DE_2024 = FIXTURES / "ons_geracao_termica_despacho_202409.csv"
DE_2022 = FIXTURES / "ons_geracao_termica_despacho_202201.csv"


def _conector(monkeypatch, arquivo: Path) -> OnsGeracaoTermicaDespacho:
    monkeypatch.setattr("src.conectores.ons_csv_mensal.criar_sessao", lambda: None)
    conector = OnsGeracaoTermicaDespacho()
    monkeypatch.setattr(
        conector, "_abrir_mes", lambda _ano, _mes: iter(arquivo.read_text(encoding="utf-8").splitlines())
    )
    return conector


@pytest.fixture
def conector(monkeypatch):
    return _conector(monkeypatch, ATUAL)


def _registros(conector, inicio, fim):
    return [
        GeracaoTermicaDespacho.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto(inicio, fim))
    ]


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    assert len(list(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-01")))) == 6
    assert len(list(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-30")))) == 8


def test_a_serie_mensal_comeca_em_2022_01():
    assert OnsGeracaoTermicaDespacho.primeiro_mes == (2022, 1)


def test_janela_de_2021_e_recusada(conector):
    with pytest.raises(ValueError, match="anual"):
        list(conector.extrair(Janela.de_texto("2021-12-01", "2022-01-31")))


def test_toda_medida_declarada_existe_no_schema_e_vem_preenchida_no_mes_atual(conector):
    """Pega erro de digitação no mapa origem -> destino: as 35 medidas chegam, nenhuma some em silêncio."""
    registro = _registros(conector, "2026-09-01", "2026-09-01")[0]

    assert len(_MEDIDAS) == 35  # 17 programadas, 15 verificadas, fator de exportação, disponibilidade, despachada
    assert all(destino in GeracaoTermicaDespacho.model_fields for destino in _MEDIDAS)
    assert all(getattr(registro, destino) is not None for destino in _MEDIDAS)


def test_usina_programada_e_verificada(conector):
    aparecida = _registros(conector, "2026-09-01", "2026-09-01")[0]

    assert aparecida.data_referencia == date(2026, 9, 1)
    assert aparecida.instante == datetime(2026, 9, 1, 0)
    assert aparecida.patamar == "LEVE"  # "Leve" no arquivo de 2026, "LEVE" nos de 2022 e 2024
    assert aparecida.submercado == "N"
    assert aparecida.nome_usina == "Aparecida"
    assert aparecida.codigo_usina == "UTE.GN.AM.027250-7.02"
    assert aparecida.codigo_usina_planejamento == 201
    assert aparecida.prog_geracao_mwmed == Decimal("146.000")
    assert aparecida.prog_ordem_merito_acima_inflex_mwmed == Decimal("86.000")
    assert aparecida.prog_inflexibilidade_mwmed == Decimal("60.000")
    assert aparecida.verif_geracao_mwmed == Decimal("145.653")
    assert aparecida.geracao_despachada_mwmed == Decimal("146.000")
    assert aparecida.combustivel == "Gás"
    assert aparecida.publicado_em == datetime(2026, 10, 2, 12, 4, 30)


def test_motivos_de_despacho_raros_sao_lidos(conector):
    registros = _registros(conector, "2026-09-01", "2026-09-30")

    garantia = next(r for r in registros if r.verif_garantia_energetica_mwmed > 0)
    substituicao = next(r for r in registros if r.prog_gsub_mwmed > 0)

    assert garantia.verif_garantia_energetica_mwmed > Decimal("0")
    assert substituicao.prog_gsub_mwmed > Decimal("0")


def test_motivo_da_restricao_vazio_e_nulo(conector):
    registros = _registros(conector, "2026-09-01", "2026-09-30")

    assert all(r.motivo_restricao is None for r in registros if r.nome_usina == "Aparecida")
    assert any(r.motivo_restricao for r in registros)


def test_tipo_de_restricao_eletrica_publicado_como_ponto_zero_vira_inteiro(conector):
    registros = _registros(conector, "2026-09-01", "2026-09-30")
    assert {r.tipo_restricao_eletrica for r in registros} <= {0, 1, 9}
    assert 9 in {r.tipo_restricao_eletrica for r in registros}  # a fixture traz uma linha com "9.0"


def test_usina_sem_codigo_de_planejamento_e_valida(conector):
    azulao = next(r for r in _registros(conector, "2026-09-01", "2026-09-30") if r.nome_usina == "Azulão")
    assert azulao.codigo_usina_planejamento is None


def test_arquivo_de_2024_nao_tem_as_seis_colunas_novas_e_elas_ficam_nulas(monkeypatch):
    conector = _conector(monkeypatch, DE_2024)

    aparecida = _registros(conector, "2024-09-01", "2024-09-01")[0]

    assert aparecida.verif_geracao_mwmed is not None
    assert aparecida.patamar == "LEVE"
    for ausente in (
        "prog_disponibilidade_mwmed",
        "geracao_despachada_mwmed",
        "combustivel",
        "motivo_restricao",
        "publicado_em",
    ):
        assert getattr(aparecida, ausente) is None, ausente


def test_arquivo_de_2022_com_codigo_ponto_zero_e_decimal_cientifico(monkeypatch):
    """Janeiro/2022: `201.0` no código e `0E-8` como zero; sem `val_fdexp`."""
    conector = _conector(monkeypatch, DE_2022)

    aparecida = _registros(conector, "2022-01-01", "2022-01-01")[0]

    assert aparecida.codigo_usina_planejamento == 201
    assert aparecida.prog_ordem_merito_mwmed == Decimal("0")
    assert aparecida.prog_geracao_mwmed == Decimal("75")
    assert aparecida.verif_fator_exportacao is None


def test_submercado_desconhecido_e_rejeitado(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-01"))))
    bruto["id_subsistema"] = "XX"

    with pytest.raises(ValidationError):
        GeracaoTermicaDespacho.model_validate(conector.transformar(bruto))


def test_ingerir_conta_as_linhas_da_janela(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-09-01", "2026-09-30"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 8
    assert execucao.linhas_invalidas == 0
