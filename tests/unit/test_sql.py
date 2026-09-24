"""O SQL do Dataform (`definitions/`) nunca é executado nos testes — mas pode ser lido.

Estes testes pegam erro de sintaxe e desvio de convenção antes da primeira
execução num BigQuery real. A compilação de verdade (refs, dependências e
config) é o job `dataform-compile` do CI; aqui o `.sqlx` é reduzido ao SQL
que ele gera, o bastante para o sqlglot ler.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
import sqlglot
from sqlglot import exp

RAIZ = Path(__file__).parents[2]
DEFINICOES = RAIZ / "definitions"
CAMADAS = ("bronze", "silver", "gold")
PROJETO = "alupdata-test"
REGIAO = "us-central1"
ARQUIVOS = [c for camada in CAMADAS for c in sorted((DEFINICOES / camada).glob("*.sqlx"))]

# ADR 012 (revisada em 11/09): a Gold de negócio é tabela, recarregada inteira a
# cada execução. A operacional segue view porque alimenta painel do Portal que
# precisa de dado atual — materializada uma vez por dia, mostraria a falha de
# hoje só amanhã. Gold nova é de negócio até entrar nesta lista.
GOLD_OPERACIONAL = {"saude_ingestao", "volumetria_lake", "custo_consultas"}

_CONFIG = re.compile(r"^config \{.*?^\}\n", re.DOTALL | re.MULTILINE)
_REF = re.compile(r'\$\{ref\("([a-z_]+)", "([a-z_]+)"\)\}')


def config(caminho: Path) -> str:
    """O bloco `config { ... }` do arquivo."""
    achado = _CONFIG.search(caminho.read_text(encoding="utf-8"))
    assert achado, f"{caminho.name} sem bloco config"
    return achado.group(0)


def renderizar(caminho: Path) -> str:
    """Reduz o `.sqlx` ao SQL que o Dataform geraria, com projeto e região de teste."""
    texto = _CONFIG.sub("", caminho.read_text(encoding="utf-8"), count=1)
    texto = _REF.sub(lambda m: f"`{PROJETO}.{m.group(1)}.{m.group(2)}`", texto)
    return (
        texto.replace("${self()}", f"`{PROJETO}.{caminho.parent.name}.{caminho.stem}`")
        .replace("${dataform.projectConfig.defaultDatabase}", PROJETO)
        .replace("${dataform.projectConfig.vars.regiao}", REGIAO)
    )


def _id(caminho: Path) -> str:
    return f"{caminho.parent.name}/{caminho.name}"


@pytest.fixture(params=ARQUIVOS, ids=[_id(c) for c in ARQUIVOS])
def arquivo(request) -> Path:
    return request.param


def test_ha_sql_para_testar():
    assert ARQUIVOS, "nenhum .sqlx encontrado — o teste não estaria verificando nada"


def test_sql_legado_nao_volta():
    """ADR 012: um mecanismo de deploy só."""
    assert not (RAIZ / "sql").exists()
    assert not (RAIZ / "scripts" / "deploy_views.py").exists()


def test_sql_e_sintaticamente_valido_no_dialeto_bigquery(arquivo):
    sqlglot.parse(renderizar(arquivo), dialect="bigquery")


def test_nada_fica_sem_resolver(arquivo):
    assert "${" not in renderizar(arquivo), "expressão do Dataform que o teste não sabe resolver"


def test_cada_camada_tem_o_tipo_e_o_dataset_certos(arquivo):
    camada = arquivo.parent.name
    bloco = config(arquivo)
    assert f'schema: "{camada}"' in bloco
    if camada == "bronze":
        assert 'type: "operations"' in bloco and "hasOutput: true" in bloco
    elif camada == "gold" and arquivo.stem not in GOLD_OPERACIONAL:
        assert 'type: "table"' in bloco, "Gold de negócio é tabela, não view nem incremental (ADR 012)"
    else:
        assert 'type: "view"' in bloco


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
    for dimensao in (
        "data_referencia",
        "submercado",
        "codigo_usina",
        "agente_ccee",
        "periodo_apuracao",
        "periodo_apuracao_ccee",
    ):
        assert dimensao in sql, f"Silver sem a dimensão comum {dimensao}"


def test_silver_tem_assertion_na_chave_de_deduplicacao(arquivo):
    if arquivo.parent.name != "silver":
        pytest.skip("regra vale só para a Silver")
    bloco = config(arquivo)
    assert "uniqueKey:" in bloco and "nonNull:" in bloco, "Silver sem portão de qualidade (ADR 012)"


def test_business_gold_requires_dependency_assertions():
    tables = [path for path in ARQUIVOS if path.parent.name == "gold" and path.stem not in GOLD_OPERACIONAL]
    assert tables
    for path in tables:
        assert "dependOnDependencyAssertions: true" in config(path), path.name


def test_compiled_gold_depends_on_silver_assertions():
    """DATAFORM_GRAPH aponta para o JSON produzido pelo job de compilação, sem GCP."""
    graph_path = os.environ.get("DATAFORM_GRAPH")
    if not graph_path:
        pytest.skip("grafo disponível no job de compilação Dataform")
    graph = json.loads(Path(graph_path).read_text(encoding="utf-8-sig"))

    def key(target):
        return tuple(target.get(field, "") for field in ("database", "schema", "name"))

    tables = [table for table in graph["tables"] if table["target"]["schema"] == "gold"]
    assert {table["target"]["name"] for table in tables} == {
        path.stem for path in ARQUIVOS if path.parent.name == "gold"
    }
    for table in tables:
        dependencies = {key(target) for target in table.get("dependencyTargets", [])}
        if table["target"]["name"] in GOLD_OPERACIONAL:
            assert not any(target[1] == "qualidade" for target in dependencies), table["target"]
            continue
        silver = {target for target in dependencies if target[1] == "silver"}
        assert silver, table["target"]
        for source in silver:
            required = {
                key(assertion["target"])
                for assertion in graph["assertions"]
                if assertion.get("parentAction") and key(assertion["parentAction"]) == source
            }
            assert required, (table["target"], source)
            assert required <= dependencies, (table["target"], required - dependencies)


def test_view_referencia_a_camada_anterior(arquivo):
    """Silver lê do Bronze; Gold lê da Silver — não pula camada.

    Exceção: view Gold de monitoramento lê `bronze._execucoes`, o log de
    execução. Ele não é fonte de dados e por isso não tem Silver.
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
    """Uma fonte com Bronze mas sem Silver é entrega incompleta (7 componentes).

    A view `_historico` (ADR 016, opção B) é a segunda Silver da mesma fonte,
    não uma fonte: fica fora da comparação.
    """
    bronze = {c.stem for c in (DEFINICOES / "bronze").glob("*.sqlx") if not c.stem.startswith("_")}
    silver = {c.stem for c in (DEFINICOES / "silver").glob("*.sqlx") if not c.stem.endswith("_historico")}
    assert bronze == silver, f"Bronze e Silver divergem: só em Bronze {bronze - silver}, só em Silver {silver - bronze}"


def test_view_de_historico_tem_bronze_e_silver_vigente():
    """`x_historico` só existe ao lado de `x`: histórico sem vigente é meia ADR 016."""
    for historico in (DEFINICOES / "silver").glob("*_historico.sqlx"):
        base = historico.stem.removesuffix("_historico")
        assert (DEFINICOES / "silver" / f"{base}.sqlx").exists(), f"{historico.name} sem a Silver vigente {base}"
        assert (DEFINICOES / "bronze" / f"{base}.sqlx").exists(), f"{historico.name} sem Bronze {base}"
        bloco = config(historico)
        assert "uniqueKey:" in bloco and "versao_publicacao" in bloco, "histórico sem assertion em (chave, versão)"


def test_information_schema_usa_a_regiao_configurada():
    """Região fixa no SQL devolve zero linhas em silêncio, não erro (ADR 011)."""
    for arquivo in ARQUIVOS:
        bruto = arquivo.read_text(encoding="utf-8")
        if "INFORMATION_SCHEMA" not in bruto:
            continue
        assert "region-${dataform.projectConfig.vars.regiao}" in bruto, (
            f"{arquivo.name} consulta INFORMATION_SCHEMA com região fora da configuração"
        )
        assert "region-us-central1" in renderizar(arquivo)


def _sem_comentarios(sql: str) -> str:
    """Só o código. Os comentários citam o que foi recusado, e disparariam falso positivo."""
    return "\n".join(linha for linha in sql.splitlines() if not linha.strip().startswith("--"))


def test_gold_que_cruza_fontes_usa_full_outer_join():
    """INNER JOIN faria o mês recente sumir em vez de aparecer sem preço.

    A CCEE publica o PLD por fechamento, com um a dois meses de defasagem; o
    ONS publica carga no dia seguinte. Com INNER, os meses em que só há carga
    **desapareceriam da tabela** — sumiço silencioso, pior que lacuna visível.

    Este teste existe porque a troca é uma "simplificação" tentadora para quem
    lê o SQL sem conhecer a defasagem das duas origens.
    """
    sql = (DEFINICOES / "gold" / "mercado_mensal_submercado.sqlx").read_text(encoding="utf-8")
    # Só o código: o comentário da própria view cita "INNER JOIN" ao explicar
    # por que ele foi recusado.
    corpo = _sem_comentarios(sql)

    assert "FULL OUTER JOIN" in corpo
    assert "INNER JOIN" not in corpo
    # a coluna que torna a lacuna legível para quem consome
    assert "cobertura" in corpo


def test_gold_de_dominio_nao_calcula_razao_entre_series():
    """ADR 012: Gold sem KPI nesta fase.

    Preço alto com carga alta pode ser escassez, manutenção ou hidrologia.
    Escolher a fórmula que traduz isso é decisão de negócio, e os itens A5 e A6
    do Questionário dizem que ela não é objetivo desta fase.
    """
    sql = (DEFINICOES / "gold" / "mercado_mensal_submercado.sqlx").read_text(encoding="utf-8")
    corpo = _sem_comentarios(sql)

    assert "pld_medio_reais_mwh /" not in corpo
    assert "/ carga_media_mwmed" not in corpo


def test_coluna_anulavel_nao_declara_null_sozinho() -> None:
    """O DDL do BigQuery aceita `NOT NULL`, e não aceita `NULL` sozinho.

    Coluna sem restrição já é anulável. Escrever `STRING NULL` compila no
    Dataform — a compilação só resolve `ref()` — e só reprova no BigQuery, com
    "Expected ")" or "," but got keyword NULL". Foi o que derrubou três DDLs
    de Bronze no primeiro Dataform real, em 24/09.
    """
    soltos = []
    for arquivo in sorted(Path(__file__).resolve().parents[2].glob("definitions/**/*.sqlx")):
        for numero, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), start=1):
            if re.match(r"^\s+\w+\s+[A-Z0-9<>,]+\s+NULL\b", linha) and "NOT NULL" not in linha:
                soltos.append(f"{arquivo.name}:{numero}: {linha.strip()}")

    assert not soltos, "coluna com NULL solto — tire a palavra, anulável é o padrão:\n" + "\n".join(soltos)
