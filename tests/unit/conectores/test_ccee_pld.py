"""Conector CCEE/PLD — CSV anual do CKAN, período horário derivado, sem rede.

O que estes testes protegem, e que não é óbvio no código:

- o `PERIODO_COMERCIALIZACAO` é o índice da hora **dentro do mês**, 1-based;
  errar o off-by-one desloca a série inteira em uma hora;
- a CCEE publica em **ISO-8859-1**, não UTF-8;
- o submercado vem por extenso (`NORDESTE`), e o lake usa sigla (`NE`);
- o recurso do ano é descoberto pelo CKAN, não por URL escrita à mão.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_pld import CceePld, PldHorario, _data_e_hora
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_pld_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_pld.criar_sessao", lambda: None)
    conector = CceePld()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="iso-8859-1"))
    return conector


# ------------------------------------------------- o período vira data e hora


@pytest.mark.parametrize(
    ("mes", "periodo", "esperado"),
    [
        ("202601", 1, (date(2026, 1, 1), 0)),  # primeira hora do mês
        ("202601", 24, (date(2026, 1, 1), 23)),  # última hora do dia 1
        ("202601", 25, (date(2026, 1, 2), 0)),  # primeira hora do dia 2
        ("202601", 744, (date(2026, 1, 31), 23)),  # 31 dias × 24h
        ("202602", 672, (date(2026, 2, 28), 23)),  # fevereiro de 2026: 28 dias
    ],
)
def test_periodo_vira_data_e_hora(mes, periodo, esperado):
    assert _data_e_hora(mes, periodo) == esperado


def test_periodo_alem_do_fim_do_mes_e_recusado():
    """745 em janeiro não existe; aceitar em silêncio criaria 1º de fevereiro fantasma."""
    with pytest.raises(ValueError, match="período .* fora do mês"):
        _data_e_hora("202601", 745)


def test_periodo_zero_ou_negativo_e_recusado():
    with pytest.raises(ValueError, match="período .* fora do mês"):
        _data_e_hora("202601", 0)


# ------------------------------------------------------------ extração/janela


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-01")))

    assert len(registros) == 5  # 4 submercados na hora 0 + NORDESTE na hora 23
    assert {r["MES_REFERENCIA"] for r in registros} == {"202601"}


def test_janela_de_dois_dias_alcanca_a_virada_do_dia(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-02")))

    assert len(registros) == 6  # entra o período 25, que é 02/01 00h
    assert any(r["PERIODO_COMERCIALIZACAO"] == "25" for r in registros)


def test_janela_fora_do_arquivo_devolve_vazio(conector):
    assert list(conector.extrair(Janela.de_texto("2026-11-01", "2026-11-30"))) == []


def test_janela_que_cruza_o_ano_baixa_cada_ano(conector, monkeypatch):
    anos = []
    monkeypatch.setattr(conector, "_baixar_ano", lambda ano: anos.append(ano) or "")

    list(conector.extrair(Janela.de_texto("2025-12-30", "2026-01-02")))

    assert anos == [2025, 2026]


def test_ano_sem_recurso_publicado_nao_derruba_a_execucao(conector, monkeypatch):
    """A CCEE só publica o ano corrente depois do primeiro fechamento."""

    def baixar(ano):
        if ano == 2025:
            raise FileNotFoundError("recurso pld_horario_submercado_2025 não publicado")
        return FIXTURE.read_text(encoding="iso-8859-1")

    monkeypatch.setattr(conector, "_baixar_ano", baixar)

    registros = list(conector.extrair(Janela.de_texto("2025-12-30", "2026-01-01")))

    assert len(registros) == 5  # o que existe em 2026 entra; 2025 vira aviso


# -------------------------------------------------------------- transformação


def test_transformar_normaliza_submercado_e_preco(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-01"))))
    registro = PldHorario.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 1, 1)
    assert registro.hora == 0
    assert registro.submercado == "NE"  # NORDESTE por extenso vira sigla
    assert registro.pld_reais_mwh == Decimal("132.03")
    assert registro.periodo_apuracao == "2026-01"


def test_os_quatro_submercados_viram_as_siglas_do_lake(conector):
    registros = [
        PldHorario.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto("2026-01-01", "2026-01-01"))
    ]

    assert {r.submercado for r in registros} == {"N", "NE", "S", "SE"}


def test_submercado_desconhecido_e_rejeitado():
    with pytest.raises(ValueError, match="submercado desconhecido"):
        PldHorario.model_validate(
            {
                "data_referencia": "2026-01-01",
                "hora": 0,
                "submercado": "CENTRO-OESTE",
                "periodo_apuracao": "2026-01",
                "periodo_comercializacao": 1,
                "pld_reais_mwh": "100",
            }
        )


def test_pld_negativo_e_rejeitado():
    """O PLD tem piso regulatório positivo; negativo é erro de origem, não preço."""
    with pytest.raises(ValueError):
        PldHorario.model_validate(
            {
                "data_referencia": "2026-01-01",
                "hora": 0,
                "submercado": "NE",
                "periodo_apuracao": "2026-01",
                "periodo_comercializacao": 1,
                "pld_reais_mwh": "-1",
            }
        )


def test_hora_fora_do_dia_e_rejeitada():
    with pytest.raises(ValueError):
        PldHorario.model_validate(
            {
                "data_referencia": "2026-01-01",
                "hora": 24,
                "submercado": "NE",
                "periodo_apuracao": "2026-01",
                "periodo_comercializacao": 1,
                "pld_reais_mwh": "100",
            }
        )


# ------------------------------------------------------------------- descoberta


def test_recurso_do_ano_vem_do_ckan_e_nao_de_url_fixa(conector, monkeypatch):
    """A CCEE republica arquivo e o endereço do recurso muda; URL fixa quebra calada."""
    pacote = {
        "result": {
            "resources": [
                {"name": "pld_horario_submercado_2025", "url": "https://exemplo/2025", "format": "CSV"},
                {"name": "pld_horario_submercado_2026", "url": "https://exemplo/2026", "format": "CSV"},
            ]
        }
    }
    monkeypatch.setattr(conector, "_pacote", lambda: pacote["result"])

    assert conector._url_do_ano(2026) == "https://exemplo/2026"


def test_ano_ausente_no_ckan_levanta_erro_nomeado(conector, monkeypatch):
    monkeypatch.setattr(conector, "_pacote", lambda: {"resources": []})

    with pytest.raises(FileNotFoundError, match="2026"):
        conector._url_do_ano(2026)


# ------------------------------------------------------------------- ingestão


def test_ingerir_conta_as_linhas_da_janela(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-02"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 6
    assert execucao.linhas_invalidas == 0
