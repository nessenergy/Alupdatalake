"""O SQL de `sql/` nunca é executado nos testes — mas pode ser lido.

Estes testes pegam erro de sintaxe e desvio de convenção **antes** do primeiro
`make deploy-views` num BigQuery real, que é onde o erro sairia caro.
"""

from pathlib import Path

import pytest
import sqlglot
from scripts.deploy_views import CAMADAS, RAIZ_SQL, arquivos, renderizar
from sqlglot import exp

ARQUIVOS = arquivos(list(CAMADAS))


def _id(caminho: Path) -> str:
    return f"{caminho.parent.name}/{caminho.name}"


@pytest.fixture(params=ARQUIVOS, ids=[_id(c) for c in ARQUIVOS])
def arquivo(request) -> Path:
    return request.param


def test_ha_sql_para_testar():
    assert ARQUIVOS, "nenhum .sql encontrado — o teste não estaria verificando nada"


def test_sql_e_sintaticamente_valido_no_dialeto_bigquery(arquivo):
    sqlglot.parse(renderizar(arquivo), dialect="bigquery")


def test_placeholders_todos_resolvidos(arquivo):
    assert "${" not in renderizar(arquivo), "placeholder não substituído pelo deploy"


def test_bronze_e_particionado_e_clusterizado(arquivo):
    if arquivo.parent.name != "bronze":
        pytest.skip("regra vale só para o Bronze")
    sql = renderizar(arquivo).upper()
    assert "PARTITION BY" in sql, "tabela Bronze sem partição faz o BigQuery varrer tudo"
    assert "CLUSTER BY" in sql


def test_bronze_carrega_as_colunas_tecnicas(arquivo):
    if arquivo.parent.name != "bronze" or arquivo.name.startswith("_"):
        pytest.skip("regra vale para as tabelas Bronze de fonte")
    sql = renderizar(arquivo)
    for coluna in ("_ingestao_id", "_ingestao_timestamp", "_fonte", "_schema_versao"):
        assert coluna in sql, f"Bronze sem {coluna}: o lote fica sem rastreio"


def test_silver_deduplica_e_expoe_as_dimensoes_comuns(arquivo):
    if arquivo.parent.name != "silver":
        pytest.skip("regra vale só para a Silver")
    sql = renderizar(arquivo)
    assert "QUALIFY" in sql.upper(), "Silver sem dedup: reprocessar duplicaria"
    for dimensao in ("data_referencia", "submercado", "codigo_usina", "agente_ccee", "periodo_apuracao"):
        assert dimensao in sql, f"Silver sem a dimensão comum {dimensao}"


def test_view_referencia_a_camada_anterior(arquivo):
    """Silver lê do Bronze; Gold lê da Silver — não pula camada.

    Exceção: view Gold de monitoramento lê `bronze._execucoes`, o log de
    execução. Ele não é fonte de dados e por isso não tem Silver — deduplicar
    ou higienizar um log de execução não faz sentido.
    """
    camada = arquivo.parent.name
    if camada == "bronze":
        pytest.skip("Bronze não referencia camada anterior")
    anterior = {"silver": "bronze", "gold": "silver"}[camada]
    tabelas = [
        t.sql(dialect="bigquery")
        for arvore in sqlglot.parse(renderizar(arquivo), dialect="bigquery")
        if arvore
        for t in arvore.find_all(exp.Table)
    ]
    if camada == "gold" and any("_execucoes" in t for t in tabelas):
        assert not any(f".{anterior}." in t for t in tabelas), (
            "view de monitoramento não deve misturar o log de execução com dado de negócio"
        )
        return
    assert any(f".{anterior}." in t for t in tabelas), f"{camada} deveria ler de {anterior}: {tabelas}"


def test_toda_camada_tem_o_mesmo_conjunto_de_fontes():
    """Uma fonte com Bronze mas sem Silver é entrega incompleta (7 componentes)."""
    bronze = {c.stem for c in (RAIZ_SQL / "bronze").glob("*.sql") if not c.stem.startswith("_")}
    silver = {c.stem for c in (RAIZ_SQL / "silver").glob("*.sql")}
    assert bronze == silver, f"Bronze e Silver divergem: só em Bronze {bronze - silver}, só em Silver {silver - bronze}"


def test_information_schema_usa_a_regiao_configurada():
    """Região fixa no SQL devolve zero linhas em silêncio, não erro.

    O `INFORMATION_SCHEMA` do BigQuery é escopado por região. Uma view que
    consulte `region-us` num projeto em `southamerica-east1` (ADR 009) não
    falha: devolve vazio. O painel de custo mostraria R$ 0,00 para sempre,
    parecendo funcionar — que é pior do que quebrar.
    """
    for arquivo in arquivos(list(CAMADAS)):
        bruto = arquivo.read_text(encoding="utf-8")
        if "INFORMATION_SCHEMA" not in bruto:
            continue
        assert "region-${regiao}" in bruto, (
            f"{arquivo.name} consulta INFORMATION_SCHEMA com região fora da configuração; "
            "use `region-${regiao}` para acompanhar o ambiente"
        )
        # E o valor renderizado precisa ser a região de verdade, não o literal.
        assert "region-southamerica-east1" in renderizar(arquivo)
