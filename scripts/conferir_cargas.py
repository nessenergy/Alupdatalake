"""Conferência das cargas no BigQuery: contagens e datas, somente leitura.

Roda no workflow `Conferir cargas` com a SA de deploy (ADR 015), para ninguém
depender de `gcloud auth` pessoal. A lista de consultas é constante deste
arquivo; nada vindo de fora vira SQL. Só SELECT e WITH passam por
`executar_consulta`. É conferência, não gate: tabela ausente ou consulta com
erro vira linha no relatório e o código de saída continua 0.

    uv run python -m scripts.conferir_cargas
"""

from __future__ import annotations

import logging
import os
import re
import sys
from dataclasses import dataclass
from string import Template
from typing import Any

from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from src.core.config import get_settings
from src.core.observabilidade import configurar_logging
from src.core.seguranca import sanitizar

configurar_logging()
logger = logging.getLogger("conferir-cargas")

# Aditivo 01 (itens 12 a 19) e Onda 1: as Silver conferidas, com o nome da view e o rótulo do conector.
SILVER_ADITIVO = (
    "ons_dados_hidrologicos",
    "ons_energia_vertida_turbinavel",
    "ons_geracao_termica_despacho",
    "ons_fator_capacidade",
    "ons_programacao_previsao",
    "ons_balanco_dessem",
    "ons_carga_programada",
    "ons_carga_verificada",
)
SILVER_ONDA_1 = (
    "inmet_precipitacao",
    "ons_bacia_contorno",
    "ons_demanda_maxima",
    "aneel_tarifas",
    "ace_prc",
    "bcb_igpm",
)
SILVER = SILVER_ADITIVO + SILVER_ONDA_1
GOLD = (
    "igpm_mensal",
    "tarifa_vigente_distribuidora",
    "prc_vigente_comercializadora",
    "demanda_maxima_mensal_subsistema",
)

_PROIBIDAS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|CALL|EXECUTE|EXPORT|LOAD)\b", re.IGNORECASE
)


@dataclass(frozen=True)
class Item:
    rotulo: str
    sql: str


Conjunto = tuple[str, list[Item]]


def validar_sql(sql: str) -> None:
    """Recusa o que não é leitura pura: só SELECT/WITH, sem `;`, comentário, DML ou DDL."""
    if not re.match(r"\s*(SELECT|WITH)\b", sql, re.IGNORECASE):
        raise ValueError("consulta recusada: só SELECT ou WITH")
    if ";" in sql or "--" in sql or "/*" in sql:
        raise ValueError("consulta recusada: `;` e comentário não são permitidos")
    if achado := _PROIBIDAS.search(sql):
        raise ValueError(f"consulta recusada: {achado.group(1).upper()} não é leitura")


def executar_consulta(cliente: Any, sql: str) -> list[dict[str, Any]]:
    """Valida e roda uma consulta; devolve as linhas como dicionários."""
    validar_sql(sql)
    job = cliente.query(sql, job_config=bigquery.QueryJobConfig(use_query_cache=True))
    return [dict(linha.items()) for linha in job.result()]


def _sql(modelo: str, **valores: str) -> str:
    """Preenche `$nome` do modelo com nomes de tabela e conector que saem de constantes e da configuração."""
    return Template(modelo).substitute(valores)


def montar_conjuntos(projeto: str, bronze: str, silver: str, gold: str) -> list[Conjunto]:
    """Os conjuntos de conferência; os nomes de projeto e dataset vêm da configuração."""

    def tabela(dataset: str, nome: str) -> str:
        return f"`{projeto}.{dataset}.{nome}`"

    execucoes = tabela(bronze, "_execucoes")
    conectores = ", ".join(f"'{nome}'" for nome in SILVER)

    silver_itens = [
        Item(
            nome,
            _sql(
                "SELECT COUNT(*) AS linhas, MIN(data_referencia) AS data_min, MAX(data_referencia) AS data_max FROM $t",
                t=tabela(silver, nome),
            ),
        )
        for nome in SILVER
    ]
    gold_itens = [Item(nome, _sql("SELECT COUNT(*) AS linhas FROM $t", t=tabela(gold, nome))) for nome in GOLD]
    gold_itens.append(
        Item(
            "precipitacao_diaria_estacao",
            _sql(
                "SELECT COUNT(*) AS linhas, COUNT(DISTINCT estacao) AS estacoes, "
                "COUNT(DISTINCT IF(bacia IS NOT NULL, estacao, NULL)) AS estacoes_com_bacia, "
                "COUNT(DISTINCT bacia) AS bacias, "
                "COUNT(DISTINCT IF(bacia_proxima IS NOT NULL, estacao, NULL)) AS estacoes_com_bacia_proxima, "
                "MAX(distancia_bacia_km) AS distancia_max_km, "
                "APPROX_QUANTILES(distancia_bacia_km, 2)[OFFSET(1)] AS distancia_mediana_km FROM $t",
                t=tabela(gold, "precipitacao_diaria_estacao"),
            ),
        )
    )
    gold_itens.append(
        Item(
            "precipitacao_diaria_bacia",
            _sql(
                "SELECT COUNT(*) AS linhas, COUNT(DISTINCT bacia) AS bacias, MIN(data_referencia) AS data_min, "
                "MAX(data_referencia) AS data_max, COUNTIF(estacoes_validas = 0) AS dias_sem_estacao_completa FROM $t",
                t=tabela(gold, "precipitacao_diaria_bacia"),
            ),
        )
    )
    silver_itens.append(
        Item(
            "bcb_igpm_ultimos_3_meses",
            _sql(
                "SELECT STRING_AGG(CONCAT(FORMAT_DATE('%Y-%m', data_referencia), '=', "
                "CAST(variacao_percentual_mes AS STRING)), "
                "' | ' ORDER BY data_referencia) AS variacao_percentual_mes FROM "
                "(SELECT data_referencia, variacao_percentual_mes FROM $t ORDER BY data_referencia DESC LIMIT 3)",
                t=tabela(silver, "bcb_igpm"),
            ),
        )
    )
    execucao_itens = [
        Item(
            "ultima_execucao",
            _sql(
                "SELECT CONCAT(fonte, '_', entidade) AS conector, status, linhas_extraidas, linhas_invalidas, "
                "linhas_carregadas, DATE(encerrada_em) AS data_execucao "
                "FROM $e WHERE CONCAT(fonte, '_', entidade) IN ($c) AND encerrada_em IS NOT NULL "
                "QUALIFY ROW_NUMBER() OVER (PARTITION BY fonte, entidade ORDER BY encerrada_em DESC) = 1 "
                "ORDER BY conector",
                e=execucoes,
                c=conectores,
            ),
        ),
        Item(
            "ultimo_erro",
            _sql(
                "SELECT CONCAT(fonte, '_', entidade) AS conector, DATE(encerrada_em) AS data_execucao, "
                "SUBSTR(erro, 1, 200) AS erro "
                "FROM $e WHERE CONCAT(fonte, '_', entidade) IN ($c) AND erro IS NOT NULL "
                "AND encerrada_em >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 DAY) "
                "QUALIFY ROW_NUMBER() OVER (PARTITION BY fonte, entidade ORDER BY encerrada_em DESC) = 1 "
                "ORDER BY conector",
                e=execucoes,
                c=conectores,
            ),
        ),
        Item(
            "erros_3_dias",
            _sql(
                "SELECT CONCAT(fonte, '_', entidade) AS conector, COUNT(*) AS execucoes_erro FROM $e "
                "WHERE status = 'ERRO' AND iniciada_em >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 DAY) "
                "GROUP BY conector ORDER BY conector",
                e=execucoes,
            ),
        ),
    ]
    saude_itens = [
        Item(
            "saude_ingestao",
            _sql(
                "SELECT situacao, COUNT(*) AS fontes FROM $t GROUP BY situacao ORDER BY situacao",
                t=tabela(gold, "saude_ingestao"),
            ),
        )
    ]
    bacia_itens = [
        Item(
            "poligonos",
            _sql(
                "SELECT COUNT(DISTINCT nome_bacia) AS poligonos, "
                "STRING_AGG(DISTINCT nome_bacia, ', ' ORDER BY nome_bacia) AS nomes FROM $c",
                c=tabela(silver, "ons_bacia_contorno"),
            ),
        ),
        Item(
            "cruzamento_ear",
            _sql(
                "WITH ear AS (SELECT DISTINCT bacia FROM $e), "
                "chaves AS (SELECT DISTINCT bacia_chave FROM $c) "
                "SELECT COUNT(*) AS nomes_ear, COUNTIF(c.bacia_chave IS NOT NULL) AS casam "
                "FROM ear AS e LEFT JOIN chaves AS c ON c.bacia_chave = e.bacia",
                e=tabela(silver, "ons_ear_bacia"),
                c=tabela(silver, "ons_bacia_contorno"),
            ),
        ),
    ]
    return [
        ("Silver por fonte", silver_itens),
        ("Gold", gold_itens),
        ("Última execução por conector", execucao_itens),
        ("Saúde da ingestão", saude_itens),
        ("Bacias", bacia_itens),
    ]


def rodar(cliente: Any, conjuntos: list[Conjunto]) -> list[tuple[str, list[dict[str, Any]]]]:
    """Roda cada item isolado: ausente ou erro vira linha, nunca derruba os demais."""
    secoes = []
    for titulo, itens in conjuntos:
        linhas: list[dict[str, Any]] = []
        for item in itens:
            try:
                resultado = executar_consulta(cliente, item.sql)
            except NotFound:
                linhas.append({"item": item.rotulo, "resultado": "ausente"})
                continue
            except Exception as erro:  # conferência, não gate: o relatório mostra a falha
                linhas.append({"item": item.rotulo, "resultado": "erro: " + sanitizar(erro, limite=200)})
                continue
            if not resultado:
                linhas.append({"item": item.rotulo, "resultado": "sem linhas"})
            # O texto de erro gravado pela ingestão vai para o resumo do GitHub: passa pelo sanitizador.
            linhas.extend(
                {
                    "item": item.rotulo,
                    **{k: sanitizar(v, limite=200) if isinstance(v, str) else v for k, v in linha.items()},
                }
                for linha in resultado
            )
        secoes.append((titulo, linhas))
    return secoes


def renderizar(secoes: list[tuple[str, list[dict[str, Any]]]]) -> str:
    """Uma seção `##` por conjunto, com uma tabela Markdown de colunas na ordem de aparição."""
    blocos = []
    for titulo, linhas in secoes:
        colunas: list[str] = []
        for linha in linhas:
            colunas.extend(c for c in linha if c not in colunas)
        corpo = [f"## {titulo}", ""]
        if colunas:
            corpo.append("| " + " | ".join(colunas) + " |")
            corpo.append("|" + "---|" * len(colunas))
            for linha in linhas:
                celulas = (str(linha.get(c, "")).replace("|", "/").replace("\n", " ") for c in colunas)
                corpo.append("| " + " | ".join(celulas) + " |")
        blocos.append("\n".join(corpo))
    return "\n\n".join(blocos)


def conferir(cliente: Any, conjuntos: list[Conjunto]) -> str:
    """Roda tudo, imprime e, se `GITHUB_STEP_SUMMARY` existir, acrescenta ao resumo."""
    texto = renderizar(rodar(cliente, conjuntos))
    print(texto)
    if resumo := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(resumo, "a", encoding="utf-8") as arquivo:
            arquivo.write(texto + "\n")
    return texto


def main() -> int:
    cfg = get_settings()
    try:
        cliente = bigquery.Client(project=cfg.gcp_project_id)
    except Exception as erro:
        logger.error("Não consegui criar o cliente do BigQuery: %s", sanitizar(erro))
        return 1
    conferir(
        cliente,
        montar_conjuntos(cfg.gcp_project_id, cfg.bq_dataset_bronze, cfg.bq_dataset_silver, cfg.bq_dataset_gold),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
