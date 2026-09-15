"""Conector CCEE/varejista consumidor — consumo das cargas de varejo, sem rede.

A chave tem cinco colunas: um varejista atende cargas em várias UFs e
distribuidoras no mesmo mês. (mês, perfil) sozinho duplica 2.465 vezes no
arquivo real — é o que o teste de chave protege.
"""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_varejista_consumidor import CceeVarejistaConsumidor, ConsumoVarejista
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_varejista_consumidor_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeVarejistaConsumidor()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [{"name": "varejista_consumidor_2026", "url": "u", "last_modified": "2026-09-01T14:00:00"}]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_o_mesmo_varejista_tem_uma_linha_por_uf_e_distribuidora(conector):
    registros = [
        ConsumoVarejista.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))
    ]
    alfa = [r for r in registros if r.codigo_perfil == "500"]

    assert {(r.uf_carga, r.codigo_perfil_conectado) for r in alfa} == {("PR", "81"), ("SC", "82")}


def test_transformar_converte_submercado_e_tipa_consumo(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))))
    registro = ConsumoVarejista.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.submercado == "S"  # SUL vira sigla
    assert registro.uf_carga == "PR"
    assert registro.sigla_perfil_conectado == "DIST PR"
    assert registro.quantidade_parcelas_carga == 150
    assert registro.consumo_total == Decimal("4974.494964")


def test_conectado_vazio_vira_nulo(conector):
    registros = [
        ConsumoVarejista.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))
    ]
    sem_conectado = [r for r in registros if r.codigo_perfil_conectado is None]

    assert len(sem_conectado) == 1
    assert sem_conectado[0].sigla_perfil_conectado is None


def test_consumo_negativo_e_rejeitado():
    with pytest.raises(ValueError):
        ConsumoVarejista.model_validate(
            {
                "data_referencia": "2026-07-01",
                "periodo_apuracao_ccee": "2026-07",
                "versao_publicacao": "2026-09-01",
                "codigo_perfil": "1",
                "sigla_perfil": "X",
                "nome_empresarial": "X",
                "uf_carga": "SP",
                "submercado": "SE",
                "quantidade_parcelas_carga": 1,
                "consumo_total": "-1",
            }
        )


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 5
    assert execucao.linhas_invalidas == 0
