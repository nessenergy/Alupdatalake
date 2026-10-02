"""Conector ANEEL — tarifas homologadas das distribuidoras: CSV único em stream, sem rede.

A fixture tem 11 linhas reais do arquivo de 02/10/2026: tarifa de aplicação e base econômica,
TE zero escrita `,00`, REH vazia, acessante vazio, despacho no lugar da resolução, duas vigências
da mesma chave (REH diferentes) e uma TE preenchida.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.aneel_tarifas import AneelTarifas, Tarifa
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "aneel_tarifas.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.aneel_tarifas.criar_sessao", lambda: None)
    conector = AneelTarifas()
    monkeypatch.setattr(conector, "_abrir", lambda: iter(FIXTURE.read_text(encoding="utf-8").splitlines()))
    return conector


def _registros(conector, inicio="2000-01-01", fim="2026-12-31"):
    return [Tarifa.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto(inicio, fim))]


def test_a_janela_recorta_pelo_inicio_da_vigencia(conector):
    assert len(list(conector.extrair(Janela.de_texto("2000-01-01", "2026-12-31")))) == 11
    assert len(list(conector.extrair(Janela.de_texto("2026-01-01", "2026-12-31")))) == 6
    assert len(list(conector.extrair(Janela.de_texto("2026-09-22", "2026-09-22")))) == 2  # pontas incluídas
    assert list(conector.extrair(Janela.de_texto("2020-01-01", "2020-12-31"))) == []


def test_vigencia_que_comecou_antes_da_janela_mas_ainda_vale_fica_de_fora(conector):
    """A janela é de início de vigência, não de sobreposição (decisão documentada no dicionário)."""
    em_vigor = {r.data_referencia for r in _registros(conector, "2026-09-01", "2026-09-30")}
    assert em_vigor == {date(2026, 9, 22)}


def test_tarifa_de_aplicacao_com_te_zero(conector):
    primeira = _registros(conector)[0]

    assert primeira.data_referencia == date(2010, 2, 3)  # início da vigência
    assert primeira.data_geracao == date(2026, 10, 2)
    assert primeira.fim_vigencia == date(2011, 2, 2)
    assert primeira.reh == "RESOLUÇÃO HOMOLOGATÓRIA Nº 0.937, DE 2 DE FEVEREIRO DE 2010"
    assert primeira.sigla_distribuidora == "CPFL JAGUARI"
    assert primeira.cnpj_distribuidora == "53859112000169"
    assert primeira.base_tarifaria == "Tarifa de Aplicação"
    assert primeira.subgrupo == "A2"
    assert primeira.modalidade == "Azul"
    assert primeira.detalhe == "APE"
    assert primeira.posto == "Fora ponta"
    assert primeira.unidade == "kW"
    assert primeira.tusd == Decimal("1.85")
    assert primeira.te == Decimal("0.00")  # `,00` é zero de verdade, não vazio


def test_te_preenchida_em_mwh(conector):
    elfsm = next(
        r
        for r in _registros(conector)
        if r.sigla_distribuidora == "ELFSM" and r.base_tarifaria == "Tarifa de Aplicação"
    )

    assert elfsm.unidade == "MWh"
    assert elfsm.tusd == Decimal("75.94")
    assert elfsm.te == Decimal("318.70")


def test_nao_se_aplica_e_preservado_como_a_origem_publica(conector):
    """O Bronze é fiel: a limpeza (`Não se aplica` vira NULL) é da Silver."""
    primeira = _registros(conector)[0]
    assert primeira.classe == "Não se aplica"
    assert primeira.subclasse == "Não se aplica"
    assert primeira.acessante == "Não se aplica"


def test_reh_e_acessante_vazios_viram_nulos(conector):
    registros = _registros(conector)
    sem_reh = next(r for r in registros if r.sigla_distribuidora == "CEA" and r.data_referencia == date(2026, 4, 13))
    sem_acessante = next(r for r in registros if r.sigla_distribuidora == "Neoenergia Brasília")

    assert sem_reh.reh is None
    assert sem_acessante.acessante is None


def test_despacho_ocupa_o_lugar_da_resolucao(conector):
    despacho = next(r for r in _registros(conector) if r.data_referencia == date(2018, 11, 30))
    assert despacho.reh.startswith("DESPACHO Nº 2.783")
    assert despacho.acessante == "UHE COARACY NUNES"


def test_mesma_chave_com_duas_resolucoes_chega_inteira(conector):
    """O conector não decide qual REH vale: a Silver guarda as duas, a Gold escolhe a vigência mais nova."""
    eac = [r for r in _registros(conector) if r.sigla_distribuidora == "EAC"]

    assert {r.data_referencia for r in eac} == {date(2026, 1, 1), date(2026, 8, 26)}
    assert {r.fim_vigencia for r in eac} == {date(2026, 12, 12)}
    assert len({r.reh for r in eac}) == 2


def test_base_economica_chega_junto_com_a_tarifa_de_aplicacao(conector):
    assert {r.base_tarifaria for r in _registros(conector)} == {"Tarifa de Aplicação", "Base Econômica"}


def test_cabecalho_sem_coluna_esperada_e_erro_claro(conector, monkeypatch):
    monkeypatch.setattr(conector, "_abrir", lambda: iter(['"DatGeracaoConjuntoDados";"SigAgente"', '"2026-10-02";"X"']))
    with pytest.raises(ValueError, match="DscREH"):
        list(conector.extrair(Janela.de_texto("2026-01-01", "2026-12-31")))


def test_arquivo_vazio_e_erro(conector, monkeypatch):
    """Resposta sem cabeçalho não pode fechar em SUCESSO com zero linha: escaparia do alerta de silêncio."""
    monkeypatch.setattr(conector, "_abrir", lambda: iter([]))
    with pytest.raises(ValueError, match="vazio"):
        list(conector.extrair(Janela.de_texto("2026-01-01", "2026-12-31")))


def test_cnpj_precisa_ter_catorze_digitos(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2000-01-01", "2026-12-31"))))
    bruto["NumCNPJDistribuidora"] = "123"
    with pytest.raises(ValidationError):
        Tarifa.model_validate(conector.transformar(bruto))


def test_valor_ilegivel_e_recusado(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2000-01-01", "2026-12-31"))))
    bruto["VlrTUSD"] = "abc"
    with pytest.raises(ValueError):
        conector.transformar(bruto)


def test_esta_registrado():
    assert (AneelTarifas.fonte, AneelTarifas.entidade) == ("aneel", "tarifas")
