"""Conector CCEE/agente — lista mensal de agentes, sem rede.

Linhas sintéticas no formato real (lido em 14/09). A fixture é montada em bytes
porque o arquivo verdadeiro mistura UTF-8 e ISO-8859-1 linha a linha, e é isso
que o teste de acentuação protege.
"""

from __future__ import annotations

import io
from datetime import date

import pytest
from src.conectores.ccee_agente import AgenteCcee, CceeAgente
from src.core.execucao import Janela

CABECALHO = (
    b"CNPJ;MES_REFERENCIA;SIGLA_AGENTE;RAZAO_SOCIAL;CLASSE_AGENTE;"
    b"SITUACAO_COMERCIALIZADOR;SITUACAO_VAREJISTA;ESTADO;CATEGORIA_AGENTE;INDICADOR_VAREJISTA\n"
)
LINHAS = [
    (
        "11111111000111;202601;ALFA;ALFA COMERCIALIZADORA LTDA;Comercializador;"
        "Autorizado;Aprovada;SP;Comercialização;Sim"
    ).encode(),
    "22222222000122;202601;BETA;BETA ENERGIA S.A.;Gerador;;;MG;Geração;Não".encode("iso-8859-1"),
    "33333333000133;202601;GAMA;GAMA INDÚSTRIA LTDA;Consumidor Livre;;;PR;Consumo;Não".encode("iso-8859-1"),
    (
        "11111111000111;202602;ALFA;ALFA COMERCIALIZADORA LTDA;Comercializador;"
        "Autorizado;Aprovada;SP;Comercialização;Sim"
    ).encode(),
    "44444444000144;202602;DELTA;DELTA DISTRIBUIÇÃO S.A.;Distribuidor;;;RS;Distribuição;Não".encode(),
]
CSV = CABECALHO + b"\n".join(LINHAS) + b"\n"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeAgente()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [{"name": "lista_agente_associado_2026", "url": "u", "last_modified": "2026-09-03T18:27:55"}]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(CSV))
    return conector


def test_registrado_como_ccee_agente():
    assert CceeAgente.fonte == "ccee" and CceeAgente.entidade == "agente"


def test_extrai_o_mes_pedido(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-02-01", "2026-02-28")))

    assert [r["SIGLA_AGENTE"] for r in registros] == ["ALFA", "DELTA"]


def test_acentuacao_sobrevive_nos_dois_encodings(conector):
    registros = {r["SIGLA_AGENTE"]: r for r in conector.extrair(Janela.de_texto("2026-01-01", "2026-02-28"))}

    assert registros["ALFA"]["CATEGORIA_AGENTE"] == "Comercialização"  # veio UTF-8
    assert registros["BETA"]["CATEGORIA_AGENTE"] == "Geração"  # veio ISO-8859-1
    assert registros["DELTA"]["RAZAO_SOCIAL"] == "DELTA DISTRIBUIÇÃO S.A."


def test_transformar_produz_o_registro_do_lake(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31"))))
    registro = AgenteCcee.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 1, 1)
    assert registro.periodo_apuracao_ccee == "2026-01"
    assert registro.versao_publicacao == date(2026, 9, 3)
    assert registro.cnpj == "11111111000111"
    assert registro.agente_ccee == "ALFA"
    assert registro.classe_agente == "Comercializador"
    assert registro.situacao_comercializador == "Autorizado"
    assert registro.situacao_varejista == "Aprovada"
    assert registro.uf == "SP"
    assert registro.categoria_agente == "Comercialização"
    assert registro.varejista is True


def test_situacao_vazia_vira_nulo_e_nao_string_vazia(conector):
    janela = Janela.de_texto("2026-01-01", "2026-01-31")
    registros = [AgenteCcee.model_validate(conector.transformar(b)) for b in conector.extrair(janela)]
    beta = next(r for r in registros if r.agente_ccee == "BETA")

    assert beta.situacao_comercializador is None
    assert beta.situacao_varejista is None
    assert beta.varejista is False


def test_classe_desconhecida_e_rejeitada():
    with pytest.raises(ValueError):
        AgenteCcee.model_validate(
            {
                "data_referencia": "2026-01-01",
                "periodo_apuracao_ccee": "2026-01",
                "versao_publicacao": "2026-09-03",
                "cnpj": "11111111000111",
                "agente_ccee": "X",
                "razao_social": "X",
                "classe_agente": "Transmissor",  # não está entre as 7 publicadas
                "uf": "SP",
                "categoria_agente": "Consumo",
                "varejista": False,
            }
        )


def test_cnpj_com_menos_de_14_digitos_e_rejeitado():
    with pytest.raises(ValueError, match="14"):
        AgenteCcee.model_validate(
            {
                "data_referencia": "2026-01-01",
                "periodo_apuracao_ccee": "2026-01",
                "versao_publicacao": "2026-09-03",
                "cnpj": "123",
                "agente_ccee": "X",
                "razao_social": "X",
                "classe_agente": "Gerador",
                "uf": "SP",
                "categoria_agente": "Geração",
                "varejista": False,
            }
        )


def test_ingerir_em_dry_run_conta_as_linhas(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-02-28"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 5
    assert execucao.linhas_invalidas == 0
    assert execucao.linhas_carregadas == 0  # dry-run
