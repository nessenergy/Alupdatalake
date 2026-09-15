"""Conector ONS/capacidade — cadastro de unidades geradoras, sem rede."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ons_capacidade import Capacidade, OnsCapacidade
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_capacidade.csv"
JANELA = Janela.de_texto("2026-09-01", "2026-09-15")


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_capacidade.criar_sessao", lambda: None)
    conector = OnsCapacidade()
    monkeypatch.setattr(conector, "_baixar", lambda: (FIXTURE.read_text(encoding="utf-8"), date(2026, 9, 1)))
    return conector


def test_le_o_cadastro_inteiro(conector):
    assert len(list(conector.extrair(JANELA))) == 4


def test_a_janela_nao_recorta_cadastro(conector):
    """Cadastro é retrato completo; janela estreita não pode devolver menos (ADR 013)."""
    um_dia = list(conector.extrair(Janela.de_texto("2026-09-14", "2026-09-14")))
    um_mes = list(conector.extrair(Janela.de_texto("2026-08-01", "2026-09-14")))

    assert len(um_dia) == len(um_mes) == 4


def test_data_referencia_vem_do_last_modified(conector):
    bruto = next(iter(conector.extrair(JANELA)))
    registro = Capacidade.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 9, 1)


def test_submercado_e_nome_do_subsistema_com_espaco_sao_normalizados(conector):
    bruto = next(iter(conector.extrair(JANELA)))
    registro = Capacidade.model_validate(conector.transformar(bruto))

    assert registro.submercado == "N"
    assert registro.nome_subsistema == "NORTE"  # veio com espaços à direita


def test_ceg_traco_vira_codigo_usina_nulo(conector):
    registros = [Capacidade.model_validate(conector.transformar(b)) for b in conector.extrair(JANELA)]
    mmgd = next(r for r in registros if r.nome_usina == "PQU BA MMGD")

    assert mmgd.codigo_usina is None


def test_ceg_presente_preenche_codigo_usina(conector):
    registros = [Capacidade.model_validate(conector.transformar(b)) for b in conector.extrair(JANELA)]
    balbina = next(r for r in registros if r.nome_usina == "BALBINA")

    assert balbina.codigo_usina == "UHE.PH.AM.000190-2.01"


def test_datas_vazias_viram_nulas_e_preenchidas_sao_parseadas(conector):
    registros = [Capacidade.model_validate(conector.transformar(b)) for b in conector.extrair(JANELA)]
    balbina = next(r for r in registros if r.nome_usina == "BALBINA")

    assert balbina.data_entrada_teste is None
    assert balbina.data_desativacao is None
    assert balbina.data_entrada_operacao == date(1989, 11, 13)


def test_data_desativacao_preenchida_quando_a_origem_declara(conector):
    registros = [Capacidade.model_validate(conector.transformar(b)) for b in conector.extrair(JANELA)]
    reversivel = next(r for r in registros if r.nome_usina == "PIRATININGA REV")

    assert reversivel.data_desativacao == date(2020, 1, 10)


def test_submercado_desconhecido_e_rejeitado():
    with pytest.raises(ValueError, match="submercado desconhecido"):
        Capacidade.model_validate(_registro_minimo(submercado="CENTRO-OESTE"))


def test_itaipu_paraguai_entra_com_submercado_nulo_nao_e_rejeitada(conector):
    """A metade paraguaia de Itaipu (10 unidades, 7.000 MW) vem com
    `id_subsistema = PY` — não é um dos quatro submercados do SIN, mas
    continua sendo o maior ativo de geração do cadastro. Diferente do
    `ons_carga` (onde submercado é a chave do fato e sigla fora da lista é
    dado que não deveria existir), aqui submercado é atributo de localização:
    o ativo entra com `submercado = NULL`, não como linha inválida — omiti-lo
    subestimaria a capacidade instalada do SIN."""
    registros = [Capacidade.model_validate(conector.transformar(b)) for b in conector.extrair(JANELA)]
    itaipu = next(r for r in registros if r.nome_usina == "ITAIPU 50 HZ")

    assert itaipu.submercado is None
    assert itaipu.potencia_efetiva == Decimal("700")


def test_sigla_inventada_de_submercado_continua_rejeitada():
    """PY é o único caso conhecido de sigla fora de N/NE/S/SE que não é erro;
    qualquer outra sigla nova é a origem mudando o contrato, e continua
    contando como linha inválida."""
    with pytest.raises(ValueError, match="submercado desconhecido"):
        Capacidade.model_validate(_registro_minimo(submercado="XX"))


def test_ingerir_carrega_o_cadastro(conector):
    execucao = conector.ingerir(JANELA)

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 4
    assert execucao.linhas_invalidas == 0


def _registro_minimo(**troca):
    base = {
        "data_referencia": "2026-09-01",
        "submercado": "N",
        "nome_subsistema": "NORTE",
        "uf": "AM",
        "nome_uf": "AMAZONAS",
        "modalidade_operacao": "TIPO I",
        "agente_proprietario": "X",
        "agente_operador": "X",
        "tipo_usina": "HIDROELÉTRICA",
        "nome_usina": "X",
        "nome_unidade_geradora": "X UG01",
        "codigo_equipamento": "EQ-1",
        "numero_unidade_geradora": "1",
        "combustivel": "Hidráulica",
        "potencia_efetiva": "10",
    }
    return base | troca
