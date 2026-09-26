"""Gera o `dados.json` do painel vivo (docs/planos/2026-09-25-painel-vivo.md).

Junta quatro fontes num retrato só, sem texto interpretativo:

- `painel/marcos.toml`: ondas, marcos e o checklist da rede, editado à mão;
- `bronze._execucoes` de dev e hml: última carga de cada entidade e os dias
  seguidos de carga da entidade de referência;
- issues abertas com a etiqueta `tipo/dependencia`: o que está com a Alup, com o
  prazo lido da linha `Prazo: AAAA-MM-DD` do corpo ou do último comentário;
- execuções do job `teste-conexao-fmb` em dev: o último resultado da rede.

Só sai metadado de execução (status, contagem e horário), nunca linha de dado.

    uv run python -m scripts.painel --saida dados.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import tomllib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("painel")

# Brasília não tem horário de verão desde 2019 (mesmo motivo de scripts/quadro.py).
BRASILIA = timezone(timedelta(hours=-3))
MARCOS = Path(__file__).resolve().parents[1] / "painel" / "marcos.toml"
META_DIAS_SEGUIDOS = 3
ESTADOS_ONDA = {"aceita", "entregue", "em_andamento", "aguarda_alup", "nao_iniciada"}
ITENS_AUTOMATICOS = {"dias_seguidos"}
ESTADOS_MARCO = {"feito", "previsto"}
ESTADOS_REDE = {"feito", "pendente"}
_PRAZO = re.compile(r"^Prazo:\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)


# ------------------------------------------------------------------ marcos


def carregar_marcos(caminho: Path = MARCOS) -> dict[str, Any]:
    """Lê e valida o arquivo de marcos; erro diz o que está errado e onde."""
    marcos = tomllib.loads(caminho.read_text(encoding="utf-8"))
    vistas: set[str] = set()
    for onda in marcos["onda"]:
        if onda["estado"] not in ESTADOS_ONDA:
            raise ValueError(f"onda {onda['numero']}: estado {onda['estado']!r} fora de {sorted(ESTADOS_ONDA)}")
        inicio, fim = onda["janela"]
        if inicio >= fim:
            raise ValueError(f"onda {onda['numero']}: janela termina antes de começar")
        if sum(i["horas"] for i in onda["item"]) != onda["horas"]:
            raise ValueError(f"onda {onda['numero']}: itens não somam as {onda['horas']}h da proposta")
        for item in onda["item"]:
            if item.get("auto") not in (None, *ITENS_AUTOMATICOS):
                raise ValueError(f"item {item['codigo']}: auto {item['auto']!r} fora de {sorted(ITENS_AUTOMATICOS)}")
            if "auto" not in item and not 0 <= item["pronto"] <= 1:
                raise ValueError(f"item {item['codigo']}: pronto {item['pronto']} fora de 0 a 1")
        repetidas = vistas.intersection(onda["entidades"])
        if repetidas:
            raise ValueError(f"onda {onda['numero']}: entidade em duas ondas: {sorted(repetidas)}")
        vistas.update(onda["entidades"])
    for marco in marcos["marco"]:
        if marco["estado"] not in ESTADOS_MARCO:
            raise ValueError(f"marco {marco['titulo']!r}: estado {marco['estado']!r} fora de {sorted(ESTADOS_MARCO)}")
    for passo in marcos["rede"]:
        if passo["estado"] not in ESTADOS_REDE:
            raise ValueError(f"rede {passo['passo']}: estado {passo['estado']!r} fora de {sorted(ESTADOS_REDE)}")
    return marcos


# ------------------------------------------------------------------ cargas


def _rotulo(execucao: dict[str, Any]) -> str:
    return f"{execucao['fonte']}_{execucao['entidade']}"


def resumir_cargas(execucoes: list[dict[str, Any]], ondas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Última execução de cada entidade, por ambiente, agrupada por onda."""
    ultima: dict[tuple[str, str], dict[str, Any]] = {}
    for e in sorted(execucoes, key=lambda e: e["iniciada_em"]):
        ultima[(_rotulo(e), e["ambiente"])] = e

    def estado(entidade: str, ambiente: str) -> dict[str, Any] | None:
        e = ultima.get((entidade, ambiente))
        if e is None:
            return None
        return {"status": e["status"], "linhas": e["linhas_carregadas"], "em": e["iniciada_em"].isoformat()}

    resumo = []
    for onda in ondas:
        entidades = [{"entidade": n, "dev": estado(n, "dev"), "hml": estado(n, "hml")} for n in onda["entidades"]]
        ok = {amb: sum(1 for e in entidades if e[amb] and e[amb]["status"] == "SUCESSO") for amb in ("dev", "hml")}
        resumo.append({"onda": onda["numero"], "entidades": entidades, "ok": {**ok, "total": len(entidades)}})
    return resumo


def dias_seguidos(execucoes: list[dict[str, Any]], entidade: str, hoje: date) -> int:
    """Dias seguidos com carga bem-sucedida em dev, terminando hoje ou ontem.

    Hoje ainda sem execução não quebra a sequência: o agendamento pode não ter
    rodado. Um dia inteiro sem sucesso quebra.
    """
    dias = {
        e["iniciada_em"].astimezone(BRASILIA).date()
        for e in execucoes
        if _rotulo(e) == entidade and e["ambiente"] == "dev" and e["status"] == "SUCESSO"
    }
    dia = hoje if hoje in dias else hoje - timedelta(days=1)
    contagem = 0
    while dia in dias:
        contagem += 1
        dia -= timedelta(days=1)
    return contagem


# ------------------------------------------------------------------ progresso global


def resumir_progresso(ondas: list[dict[str, Any]], dias: int, meta: int) -> dict[str, Any]:
    """Horas prontas sobre as horas da proposta, item a item.

    Separa o que já foi aceito, o que está em aceite (onda entregue) e o que está
    adiantado (pronto em onda ainda não entregue).
    """

    def fracao(item: dict[str, Any]) -> float:
        if item.get("auto") == "dias_seguidos":
            return min(1.0, dias / meta)
        return float(item["pronto"])

    por_onda, faixas = [], {"aceito": 0.0, "em_aceite": 0.0, "adiantado": 0.0}
    for onda in ondas:
        prontas = sum(i["horas"] * fracao(i) for i in onda["item"])
        por_onda.append({"onda": onda["numero"], "horas": onda["horas"], "prontas": prontas})
        faixa = {"aceita": "aceito", "entregue": "em_aceite"}.get(onda["estado"], "adiantado")
        faixas[faixa] += prontas
    total = sum(o["horas"] for o in ondas)
    feitas = sum(faixas.values())
    return {"horas_total": total, **faixas, "pct": 100 * feitas / total, "por_onda": por_onda}


# ------------------------------------------------------------------ dias adiantados ou atrasados


def saldo_dias(onda: dict[str, Any], fracao: float, hoje: date) -> int:
    """Dias de folga (positivo) ou de atraso (negativo) da onda.

    Entregue: fim da janela menos a data de entrega. Não entregue: dias de
    trabalho já feitos (fração pronta × duração da janela) menos os dias já
    corridos da janela; antes de a janela abrir, tudo o que está pronto é folga.
    """
    inicio, fim = onda["janela"]
    if onda.get("entregue_em"):
        return (fim - onda["entregue_em"]).days
    duracao = (fim - inicio).days
    corridos = min(max((hoje - inicio).days, 0), duracao)
    return round(fracao * duracao - corridos)


# ------------------------------------------------------------------ pendências


def _prazo(issue: dict[str, Any]) -> date | None:
    """A linha `Prazo:` mais recente: do último comentário que a tem, senão do corpo."""
    for texto in [*reversed(issue["comments"]), issue["body"] or ""]:
        achados = _PRAZO.findall(texto or "")
        if achados:
            return date.fromisoformat(achados[-1])
    return None


def resumir_pendencias(issues: list[dict[str, Any]], hoje: date) -> list[dict[str, Any]]:
    """Pendências abertas, das atrasadas às sem prazo."""
    pendencias = []
    for issue in issues:
        prazo = _prazo(issue)
        pendencias.append(
            {
                "numero": issue["number"],
                "titulo": re.sub(r"^\[ALUP\]\s*", "", issue["title"]),
                "prazo": prazo.isoformat() if prazo else None,
                "atrasada": bool(prazo and prazo < hoje),
                "dias_aberta": (hoje - issue["created_at"].astimezone(BRASILIA).date()).days,
                "url": issue["url"],
            }
        )
    return sorted(pendencias, key=lambda p: (not p["atrasada"], p["prazo"] is None, p["prazo"] or ""))


# ------------------------------------------------------------------ rede


def resumir_teste_conexao(execucoes: list[dict[str, Any]]) -> dict[str, Any]:
    """Resultado da última execução do teste de conexão."""
    if not execucoes:
        return {"estado": "nunca_rodou", "em": None}
    ultima = max(execucoes, key=lambda e: e["fim"])
    return {"estado": "passou" if ultima["sucesso"] else "falhou", "em": ultima["fim"].isoformat()}


# ------------------------------------------------------------------ entre jobs do workflow


def exportar_execucoes(execucoes: list[dict[str, Any]]) -> str:
    """Execuções em JSON, para passar do job de hml ao de publicação."""
    return json.dumps([{**e, "iniciada_em": e["iniciada_em"].isoformat()} for e in execucoes])


def importar_execucoes(texto: str) -> list[dict[str, Any]]:
    """O inverso de `exportar_execucoes`; vazio vira lista vazia (job de hml falhou)."""
    if not texto.strip():
        return []
    return [{**e, "iniciada_em": datetime.fromisoformat(e["iniciada_em"])} for e in json.loads(texto)]


# ------------------------------------------------------------------ dados.json


def _datas(valor: Any) -> Any:
    """Datas do TOML em texto ISO, para o JSON."""
    if isinstance(valor, dict):
        return {k: _datas(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_datas(v) for v in valor]
    if isinstance(valor, date):
        return valor.isoformat()
    return valor


def montar(
    marcos: dict[str, Any],
    execucoes: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    testes: list[dict[str, Any]],
    agora: datetime,
) -> dict[str, Any]:
    hoje = agora.astimezone(BRASILIA).date()
    referencia = marcos["referencia_dias_seguidos"]
    progresso = resumir_progresso(marcos["onda"], dias_seguidos(execucoes, referencia, hoje), META_DIAS_SEGUIDOS)
    fracoes = {o["onda"]: o["prontas"] / o["horas"] for o in progresso["por_onda"]}
    ondas = [
        {**{k: v for k, v in o.items() if k != "entidades"}, "saldo_dias": saldo_dias(o, fracoes[o["numero"]], hoje)}
        for o in marcos["onda"]
    ]
    return {
        "gerado_em": agora.isoformat(),
        "contrato": {"inicio": marcos["inicio_contrato"].isoformat(), "fim": marcos["fim_contrato"].isoformat()},
        "ondas": _datas(ondas),
        "marcos": _datas(marcos["marco"]),
        "cargas": resumir_cargas(execucoes, marcos["onda"]),
        "dias_seguidos": {
            "entidade": referencia,
            "dias": dias_seguidos(execucoes, referencia, hoje),
            "meta": META_DIAS_SEGUIDOS,
        },
        "progresso": progresso,
        "pendencias": resumir_pendencias(issues, hoje),
        "rede": {"checklist": _datas(marcos["rede"]), "teste_conexao": resumir_teste_conexao(testes)},
    }


# ------------------------------------------------------------------ leitura das fontes

_SQL = """
SELECT fonte, entidade, status, linhas_carregadas, iniciada_em
FROM `{projeto}.bronze._execucoes`
WHERE modo = 'FONTE' AND iniciada_em >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 14 DAY)
"""


def ler_execucoes(projetos: dict[str, str]) -> list[dict[str, Any]]:  # pragma: no cover - E/S
    from google.cloud import bigquery

    execucoes = []
    for ambiente, projeto in projetos.items():
        cliente = bigquery.Client(project=projeto)
        for linha in cliente.query(_SQL.format(projeto=projeto)).result():
            execucoes.append({"ambiente": ambiente, **dict(linha.items())})
    return execucoes


def ler_issues(repositorio: str, token: str) -> list[dict[str, Any]]:  # pragma: no cover - E/S
    import requests

    cabecalho = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    base = f"https://api.github.com/repos/{repositorio}"
    resposta = requests.get(
        f"{base}/issues",
        params={"labels": "tipo/dependencia", "state": "open", "per_page": 100},
        headers=cabecalho,
        timeout=30,
    )
    resposta.raise_for_status()
    issues = []
    for bruta in resposta.json():
        if "pull_request" in bruta:
            continue
        comentarios = []
        if bruta["comments"]:
            c = requests.get(bruta["comments_url"], params={"per_page": 100}, headers=cabecalho, timeout=30)
            c.raise_for_status()
            comentarios = [x["body"] for x in c.json()]
        issues.append(
            {
                "number": bruta["number"],
                "title": bruta["title"],
                "body": bruta["body"],
                "comments": comentarios,
                "created_at": datetime.fromisoformat(bruta["created_at"].replace("Z", "+00:00")),
                "url": bruta["html_url"],
            }
        )
    return issues


def ler_testes_conexao(projeto: str, regiao: str, job: str) -> list[dict[str, Any]]:  # pragma: no cover - E/S
    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    credenciais, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    sessao = AuthorizedSession(credenciais)
    url = f"https://run.googleapis.com/v2/projects/{projeto}/locations/{regiao}/jobs/{job}/executions"
    resposta = sessao.get(url, params={"pageSize": 20}, timeout=30)
    if resposta.status_code == 404:  # o job só existe com a rede declarada no ambiente
        return []
    resposta.raise_for_status()
    return [
        {
            "fim": datetime.fromisoformat(e["completionTime"].replace("Z", "+00:00")),
            "sucesso": e.get("succeededCount", 0) > 0,
        }
        for e in resposta.json().get("executions", [])
        if e.get("completionTime")
    ]


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - E/S
    parser = argparse.ArgumentParser(description="Gera o dados.json do painel vivo")
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument(
        "--ambiente",
        action="append",
        metavar="NOME=PROJETO",
        help="ambiente lido do BigQuery; repetível (padrão: dev e hml)",
    )
    parser.add_argument(
        "--execucoes-de", type=Path, action="append", default=[], help="execuções já exportadas por outro job"
    )
    parser.add_argument("--so-execucoes", action="store_true", help="só exporta as execuções dos ambientes")
    parser.add_argument("--repositorio", default="nessenergy/Alupdatalake")
    parser.add_argument("--regiao", default="us-central1")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    ambientes = dict(a.split("=", 1) for a in (args.ambiente or ["dev=alupar-dev-alupdata", "hml=alupar-hm-alupdata"]))
    execucoes = ler_execucoes(ambientes)
    if args.so_execucoes:
        args.saida.write_text(exportar_execucoes(execucoes), encoding="utf-8")
        logger.info("painel: %d execuções exportadas -> %s", len(execucoes), args.saida)
        return 0
    for arquivo in args.execucoes_de:
        execucoes += importar_execucoes(arquivo.read_text(encoding="utf-8") if arquivo.exists() else "")

    marcos = carregar_marcos()
    issues = ler_issues(args.repositorio, os.environ["GITHUB_TOKEN"])
    testes = ler_testes_conexao(ambientes.get("dev", "alupar-dev-alupdata"), args.regiao, "teste-conexao-fmb")
    dados = montar(marcos, execucoes, issues, testes, datetime.now(BRASILIA))
    args.saida.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    logger.info("painel: %d execuções, %d pendências -> %s", len(execucoes), len(issues), args.saida)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
