"""Conector CCEE/CVU estrutural — o único CSV com vírgula, e um CVU por ano de horizonte, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_cvu_estrutural import CceeCvuEstrutural, CvuEstrutural
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_cvu_estrutural_2026.csv"

CABECALHO = (
    "MES_REFERENCIA,ANO_HORIZONTE,CODIGO_PARCELA_USINA,SIGLA_PARCELA,TIPO_COMBUSTIVEL,"
    "LEILAO,PRODUTO,CVU_ESTRUTURAL,CODIGO_MODELO_PRECO,TERMINO_SUPRIMENTO,INICIO_SUPRIMENTO"
)


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeCvuEstrutural()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [
                {"name": "custo_variavel_unitario_estrutural_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}
            ]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_delimitador_e_virgula():
    assert CceeCvuEstrutural.delimitador == ","


def test_a_mesma_usina_tem_um_cvu_por_ano_de_horizonte(conector):
    registros = [
        CvuEstrutural.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31"))
    ]
    alfa = sorted((r.ano_horizonte, r.cvu_estrutural) for r in registros if r.codigo_parcela_usina == "986386")

    assert alfa == [(2026, Decimal("2427.25")), (2027, Decimal("2837.36"))]


def test_transformar_converte_datas_brasileiras(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31"))))
    registro = CvuEstrutural.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 1, 1)
    assert registro.inicio_suprimento == date(2020, 10, 6)
    assert registro.termino_suprimento == date(2035, 10, 5)
    assert registro.tipo_combustivel == "Diesel"
    assert registro.leilao == "2º Leilão de Energia Nova"


def test_cvu_negativo_e_rejeitado():
    with pytest.raises(ValueError):
        CvuEstrutural.model_validate(
            {
                "data_referencia": "2026-01-01",
                "periodo_apuracao_ccee": "2026-01",
                "versao_publicacao": "2026-09-01",
                "ano_horizonte": 2026,
                "codigo_parcela_usina": "1",
                "sigla_parcela": "X",
                "tipo_combustivel": "X",
                "leilao": "X",
                "produto": "X",
                "cvu_estrutural": "-1",
                "codigo_modelo_preco": "1",
            }
        )


def test_data_malformada_e_rejeitada():
    """`dd/mm/aaaa` que não bate vira `ValidationError` no schema, não `ValueError` cru em `transformar()`."""
    with pytest.raises(ValueError):
        CvuEstrutural.model_validate(
            {
                "data_referencia": "2026-01-01",
                "periodo_apuracao_ccee": "2026-01",
                "versao_publicacao": "2026-09-01",
                "ano_horizonte": 2026,
                "codigo_parcela_usina": "1",
                "sigla_parcela": "X",
                "tipo_combustivel": "X",
                "leilao": "X",
                "produto": "X",
                "cvu_estrutural": "10",
                "codigo_modelo_preco": "1",
                "inicio_suprimento": "31/13/2020",  # mês 13 não existe
            }
        )


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-02-28"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 4
    assert execucao.linhas_invalidas == 0


def test_inicio_suprimento_malformado_conta_como_invalida_sem_derrubar_o_mes(conector, monkeypatch):
    """Regressão: uma linha com `INICIO_SUPRIMENTO` malformado vira linha inválida, não crash do lote."""
    linha_ruim = (
        "202601,2026,986386,UTE Alfa,Diesel,2º Leilão de Energia Nova,2009-15,2427.25,235,05/10/2035,31/13/2020\n"
    )
    csv_com_linha_ruim = (CABECALHO + "\n" + linha_ruim).encode("utf-8")
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(csv_com_linha_ruim))

    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_invalidas == 1
