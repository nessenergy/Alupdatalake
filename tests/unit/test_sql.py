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
# Gold que lê outras Gold. Fechado e com motivo: a agregação por usina e mês já
# está feita na Gold de domínio, e refazê-la sobre a Silver duplicaria a regra.
GOLD_DERIVADA = {"indicadores_mensais"}

_CONFIG = re.compile(r"^config \{.*?^\}\n", re.DOTALL | re.MULTILINE)
_REF = re.compile(r'\$\{ref\("([a-z_]+)", "([a-z_]+)"\)\}')


def config(caminho: Path) -> str:
    """O bloco `config { ... }` do arquivo."""
    achado = _CONFIG.search(caminho.read_text(encoding="utf-8"))
    assert achado, f"{caminho.name} sem bloco config"
    return achado.group(0)


def _silencio_valores() -> str:
    """O que `silencio.valores()` (includes/silencio.js) gera, lido do próprio arquivo."""
    js = (RAIZ / "includes" / "silencio.js").read_text(encoding="utf-8")
    pares = re.findall(r"^\s+([a-z0-9_]+):\s*(\d+),", js, re.M)
    return ",\n    ".join(f"STRUCT('{c}' AS conector, {h} AS limite_h)" for c, h in pares)


def renderizar(caminho: Path) -> str:
    """Reduz o `.sqlx` ao SQL que o Dataform geraria, com projeto e região de teste."""
    texto = _CONFIG.sub("", caminho.read_text(encoding="utf-8"), count=1)
    texto = _REF.sub(lambda m: f"`{PROJETO}.{m.group(1)}.{m.group(2)}`", texto)
    return (
        texto.replace("${self()}", f"`{PROJETO}.{caminho.parent.name}.{caminho.stem}`")
        .replace("${dataform.projectConfig.defaultDatabase}", PROJETO)
        .replace("${dataform.projectConfig.vars.regiao}", REGIAO)
        .replace("${silencio.valores()}", _silencio_valores())
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
        if table["target"]["name"] in GOLD_DERIVADA:
            # Depende só de Gold de negócio; cada uma delas passa pela checagem da
            # Silver neste mesmo laço, e a garantia de qualidade vem por transitividade.
            upstream = {target for target in dependencies if target[1] != "qualidade"}
            assert upstream, table["target"]
            assert all(target[1] == "gold" and target[2] not in GOLD_OPERACIONAL for target in upstream), upstream
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
    if camada == "gold" and arquivo.stem in GOLD_DERIVADA:
        # Compõe dentro da camada, não pula: lê só Gold, nunca Bronze nem Silver.
        fisicas = [t for t in tabelas if "`" in t]  # CTE não tem projeto nem crase
        assert fisicas and all(".gold." in t for t in fisicas), f"{arquivo.name} deveria ler só Gold: {fisicas}"
        return
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


def test_silver_geracao_usina_aceita_geracao_liquida_levemente_negativa() -> None:
    """Medido no GCP em 24/09/2026: a primeira carga real de julho/2026 de
    `ccee_geracao_usina` (1.735.627 linhas) reprovou a condição antiga
    (`geracao_centro_gravidade >= 0`) em 7 linhas, todas levemente negativas
    — a menor é -0,002261 MWh (parcela 967489, NE, 12/07/2026, hora 14). A
    CCEE publica a geração **líquida** no centro de gravidade: quando a
    usina consome mais do que gera (consumo auxiliar), o valor fica
    levemente negativo — o dado é real, a premissa de "geração negativa não
    existe" (issue #110) estava errada. A condição passa a exigir
    `geracao_centro_gravidade >= -10`: aceita o consumo auxiliar e ainda
    pega inversão de sinal ou erro de unidade em qualquer usina que gere
    mais de 10 MWh na hora.
    """
    bloco = config(DEFINICOES / "silver" / "ccee_geracao_usina.sqlx")
    assert "geracao_centro_gravidade >= -10" in bloco
    assert "geracao_centro_gravidade >= 0" not in bloco


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


INDICADORES = DEFINICOES / "gold" / "indicadores_mensais.sqlx"
NOMES_DE_INDICADOR = {"taxa_corte_renovavel", "disponibilidade", "fator_capacidade", "armazenamento", "pld_real"}
# Gold de domínio que já divide duas colunas, e por quê. A lista é fechada: Gold
# nova com razão entra aqui com o motivo, ou vai para `indicadores_mensais`.
RAZAO_PERMITIDA = {
    "exposicao_mercado_mensal": "cobertura ÷ exposição, as duas em R$ e do mesmo relatório da CCEE",
}


def test_indicadores_declara_os_cinco_indicadores_e_as_assercoes():
    sql = INDICADORES.read_text(encoding="utf-8")
    corpo = _sem_comentarios(sql)

    for nome in NOMES_DE_INDICADOR:
        assert f"'{nome}' AS indicador" in corpo, nome
    assert 'uniqueKey: ["periodo_apuracao", "indicador", "submercado", "fonte"]' in sql
    assert "denominador > 0" in sql
    assert "SAFE_DIVIDE(numerador, denominador)" in corpo


def test_so_indicadores_mensais_divide_uma_serie_por_outra():
    """ADR 012: a razão mora numa tabela só, rotulada como tal; Gold de domínio agrega."""
    for arquivo in (DEFINICOES / "gold").glob("*.sqlx"):
        if arquivo.stem == "indicadores_mensais" or arquivo.stem in GOLD_OPERACIONAL or arquivo.stem in RAZAO_PERMITIDA:
            continue
        assert "SAFE_DIVIDE(" not in _sem_comentarios(arquivo.read_text(encoding="utf-8")), arquivo.name


def test_limite_de_atraso_do_portal_e_o_mesmo_do_alerta() -> None:
    """`saude_ingestao` marca ATRASADA pelo limite de silêncio do alerta (29/09).

    As duas listas — o mapa do Terraform e `includes/silencio.js` — têm de ser
    iguais, ou o Portal e o alerta discordam sobre o que é atraso.
    """
    raiz = Path(__file__).resolve().parents[2]
    tf = (raiz / "infra/modules/monitoramento/main.tf").read_text(encoding="utf-8")
    bloco = tf[tf.index('variable "conectores_criticos"') :]
    bloco = bloco[bloco.index("default") : bloco.index("\n  }\n")]
    do_alerta = dict(re.findall(r"^\s+([a-z0-9_]+)\s*=\s*(\d+)", bloco, re.M))

    js = (raiz / "includes/silencio.js").read_text(encoding="utf-8")
    js = js[js.index("const limites_horas") : js.index("};")]
    do_portal = dict(re.findall(r"^\s+([a-z0-9_]+):\s*(\d+),", js, re.M))

    assert do_alerta and do_portal == do_alerta

    saude = (raiz / "definitions/gold/saude_ingestao.sqlx").read_text(encoding="utf-8")
    assert "${silencio.valores()}" in saude
    assert "l.limite_h * 60" in saude


def test_saude_marca_fonte_que_aguarda_credencial() -> None:
    """Falta de segredo numa fonte que nunca carregou é espera da Alup, não falha (01/10).

    A decisão fica no Gold: o Portal só mostra, sem lista de fontes escrita na tela.
    """
    saude = (RAIZ / "definitions/gold/saude_ingestao.sqlx").read_text(encoding="utf-8")
    assert "AS aguardando_credencial" in saude
    assert "a.ultimo_sucesso IS NULL" in saude
    assert "secret|cofre local" in saude


def test_toda_fonte_agendada_tem_limite_de_silencio_ou_motivo() -> None:
    """Fonte mensal fora do mapa cai no padrão de 52 h e o Portal a marca como atrasada
    uma semana depois da carga (visto em 02/10 com a restrição de corte eólica).

    Só fica de fora o que não pode ter sucesso por motivo documentado.
    """
    agendadas = set(
        re.findall(
            r"^ {4}([a-z0-9_]+)\s*=\s*\{\n(?:.*\n)*?\s+cron\s*=",
            (RAIZ / "infra/modules/scheduler/main.tf").read_text(encoding="utf-8"),
            re.M,
        )
    )
    js = (RAIZ / "includes/silencio.js").read_text(encoding="utf-8")
    com_limite = set(re.findall(r"^\s+([a-z0-9_]+):\s*\d+,", js, re.M))
    # Onda 2: dependem de token ou de entrada da Alup (ADR 020, A9) e ainda não executam
    # com sucesso. Quando uma delas passar a rodar, sai desta lista e ganha limite.
    sem_sucesso_possivel = {"bbce_curva_forward", "hubspot_negocios", "tempook_boletins", "tempook_ena_prevs"}
    assert agendadas, "a regex não achou nenhuma fonte agendada"
    assert not (agendadas - com_limite - sem_sucesso_possivel)


def test_saude_trata_execucao_sem_fim_como_erro() -> None:
    """Execução morta por tempo limite deixa só a marca de início; a saúde não pode mostrar OK (29/09)."""
    caminho = Path(__file__).resolve().parents[2] / "definitions" / "gold" / "saude_ingestao.sqlx"
    sql = caminho.read_text(encoding="utf-8")
    assert "status = 'EM_EXECUCAO'" in sql
    assert "INTERVAL 40 MINUTE" in sql
    assert "NOT EXISTS" in sql


def test_silver_das_tarifas_nao_reprova_valor_negativo_que_a_aneel_publica() -> None:
    """2.433 linhas do arquivo real têm TUSD ou TE negativa; a asserção de piso em zero reprovou o Dataform (02/10)."""
    caminho = Path(__file__).resolve().parents[2] / "definitions" / "silver" / "aneel_tarifas.sqlx"
    assert ">= 0" not in caminho.read_text(encoding="utf-8").split("SELECT", 1)[0]


def test_gold_da_chuva_nao_trata_hora_sem_medicao_como_zero() -> None:
    """Hora sem medição conta em `horas_sem_medicao`; somar COALESCE(..., 0) esconderia o buraco da origem."""
    caminho = Path(__file__).resolve().parents[2] / "definitions" / "gold" / "precipitacao_diaria_estacao.sqlx"
    sql = caminho.read_text(encoding="utf-8")
    assert "horas_sem_medicao" in sql
    assert "COALESCE(precipitacao_mm" not in sql


def test_gold_da_chuva_liga_a_bacia_por_ponto_em_poligono_sem_agregar_por_bacia() -> None:
    """ADR 026: `bacia` é uma coluna ao lado da estação. Menor área desempata; LEFT JOIN não perde estação sem bacia."""
    caminho = Path(__file__).resolve().parents[2] / "definitions" / "gold" / "precipitacao_diaria_estacao.sqlx"
    sql = caminho.read_text(encoding="utf-8")
    corpo = "\n".join(linha for linha in sql.splitlines() if not linha.lstrip().startswith("--"))
    assert "ST_COVERS(" in corpo  # a borda também recebe a bacia
    assert "ST_CONTAINS(" not in corpo
    assert "b.bacia_chave" in corpo and "bacia_chave" in corpo.split("estacao_bacia AS", 1)[1]
    assert "WHERE latitude IS NOT NULL AND longitude IS NOT NULL" in corpo  # coordenada mais recente que não seja nula
    assert "ORDER BY c.area_m2 ASC" in corpo  # estação em dois polígonos: vale o menor
    assert "ST_AREA(" in corpo
    assert "LEFT JOIN contorno_vigente" in corpo  # estação fora de todo contorno continua na Gold
    assert "INNER JOIN" not in corpo
    assert "GROUP BY p.estacao, b.bacia, b.bacia_chave, p.data_referencia" in corpo  # a chuva segue por estação e dia
    assert not re.search(r"\b(AVG|SUM)\([^)]*bacia", corpo)  # nenhuma média nem soma por bacia


def test_silver_do_contorno_repara_a_geometria_e_deduplica_por_bacia_e_data() -> None:
    """6 dos 31 polígonos têm autointerseção; sem `make_valid` o BigQuery recusa a geometria."""
    caminho = Path(__file__).resolve().parents[2] / "definitions" / "silver" / "ons_bacia_contorno.sqlx"
    sql = caminho.read_text(encoding="utf-8")
    assert "ST_GEOGFROMTEXT(wkt, make_valid => TRUE)" in sql
    assert "NORMALIZE(nome_bacia, NFD)" in sql and "AS bacia_chave" in sql  # chave para cruzar com ons_ear_bacia
    assert "PARTITION BY nome_bacia, data_referencia" in sql
    assert 'uniqueKey: ["nome_bacia", "data_referencia"]' in sql
