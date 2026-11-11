"""CLI do AlupData.

O mesmo entrypoint roda no laptop, no Cloud Run Job e na DAG do Composer —
não existe caminho de código que só rode em produção.

    alupdata listar
    alupdata ingerir bcb_cambio_ptax --de 2026-01-01 --ate 2026-01-31
    alupdata ingerir bcb_cambio_ptax --ultimos-dias 7 --dry-run
    alupdata testar-conexao fmb
    alupdata testar-ccee --dia 2026-11-01
    alupdata sondar cptec
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from src.conectores.ccee_pi_sessao import testar_cadastro, testar_ccee
from src.core.banco import esquema, testar_conexao
from src.core.config import get_settings
from src.core.execucao import Janela
from src.core.observabilidade import configurar_logging
from src.core.registry import listar, obter
from src.core.sonda import SONDAS, gravar_resultado, sondar

configurar_logging()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alupdata", description="Ingestão do DataLake AlupData")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("listar", help="lista os conectores registrados")

    ingerir = sub.add_parser("ingerir", help="executa a ingestão de uma fonte")
    ingerir.add_argument("conector", help="rótulo do conector (ver `alupdata listar`)")
    ingerir.add_argument("--de", help="início da janela (YYYY-MM-DD)")
    ingerir.add_argument("--ate", help="fim da janela (YYYY-MM-DD)")
    ingerir.add_argument("--ultimos-dias", type=int, help="janela terminando ontem")
    ingerir.add_argument("--dry-run", action="store_true", help="extrai e valida sem gravar")

    replay = sub.add_parser("reprocessar-raw", help="reprocessa um objeto raw já arquivado no GCS")
    replay.add_argument("conector", help="rótulo do conector dono do raw")
    replay.add_argument("--uri", required=True, help="objeto gs:// no layout raw canônico")
    replay.add_argument("--de", required=True, help="início da janela original (YYYY-MM-DD)")
    replay.add_argument("--ate", required=True, help="fim da janela original (YYYY-MM-DD)")

    teste = sub.add_parser("testar-conexao", help="abre conexão com a DSN da fonte e roda SELECT 1")
    teste.add_argument("fonte", help="fonte do secret alupdata-<fonte>-dsn, como fmb ou comercializacao")
    ccee = sub.add_parser(
        "testar-ccee", help="uma chamada de leitura à CCEE (listarMedida) para provar credencial e certificado"
    )
    ccee.add_argument("--ponto", default="CEPITBUFPI211", help="código do ponto de medição")
    ccee.add_argument("--dia", help="dia consultado (YYYY-MM-DD); obrigatório sem --cadastro")
    ccee.add_argument(
        "--cadastro", action="store_true", help="consulta o ponto no cadastro e mostra os perfis relacionados"
    )
    ccee.add_argument("--piloto", action="store_true", help="usa o ambiente piloto da CCEE (mesmas credenciais)")
    esquema_cmd = sub.add_parser("esquema", help="lista as colunas das tabelas de um MySQL (só information_schema)")
    esquema_cmd.add_argument("fonte", help="fonte do secret alupdata-<fonte>-dsn, como portal-alup")
    esquema_cmd.add_argument("--tabelas", required=True, help="nomes das tabelas, separados por vírgula")
    sonda = sub.add_parser("sondar", help="chama os endereços de uma sonda fixa e imprime status e amostra")
    sonda.add_argument("nome", choices=sorted(SONDAS), help="sonda da lista fixa em src/core/sonda.py")
    return parser


def _janela(args: argparse.Namespace) -> Janela:
    if args.ultimos_dias:
        return Janela.ultimos_dias(args.ultimos_dias)
    if args.de and args.ate:
        return Janela.de_texto(args.de, args.ate)
    raise SystemExit("informe --de e --ate, ou --ultimos-dias")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.comando == "listar":
        for rotulo in listar():
            print(rotulo)
        return 0

    if args.comando == "testar-conexao":
        ok, mensagem = testar_conexao(args.fonte)
        print(mensagem)
        return 0 if ok else 1

    if args.comando == "testar-ccee" and args.cadastro:
        ok, mensagem = testar_cadastro(args.ponto, piloto=args.piloto)
        print(mensagem)
        return 0 if ok else 1

    if args.comando == "testar-ccee":
        if not args.dia:
            raise SystemExit("informe --dia (ou use --cadastro)")
        ok, mensagem = testar_ccee(args.ponto, args.dia, piloto=args.piloto)
        print(mensagem)
        return 0 if ok else 1

    if args.comando == "esquema":
        try:
            resultado = esquema(args.fonte, [t.strip() for t in args.tabelas.split(",")])
        except (ValueError, RuntimeError) as erro:  # a mensagem já vem sem a DSN
            print(f"{args.fonte}: {erro}")
            return 1
        # Texto, e não JSON: linha que começa com `{` vira log estruturado no Cloud Run e o workflow não a lê.
        for c in resultado.colunas:
            nulo = "NULL" if c["aceita_nulo"] else "NOT NULL"
            print(f"{c['tabela']}.{c['coluna']} | {c['tipo']} | {nulo} | {c['chave']}")
        print(f"tabelas ausentes: {', '.join(resultado.tabelas_ausentes) or 'nenhuma'}")
        return 0

    if args.comando == "sondar":
        resultados = sondar(args.nome)
        for resultado in resultados:
            print(json.dumps({"sonda": args.nome, **dataclasses.asdict(resultado)}, ensure_ascii=False))
        print(json.dumps({"sonda": args.nome, "resultado_em": gravar_resultado(args.nome, resultados)}))
        return 0

    if args.comando == "reprocessar-raw":
        conector = obter(args.conector)
        execucao = conector.reprocessar_raw(args.uri, Janela.de_texto(args.de, args.ate))
        return 0 if execucao.status == "SUCESSO" else 1

    if args.dry_run:
        get_settings().dry_run = True

    conector = obter(args.conector)
    execucao = conector.ingerir(_janela(args))
    # SEM_PERMISSAO sai com 0 de propósito: o erro fica em `_execucoes` e no log, sem o alerta de job falho
    return 0 if execucao.status in ("SUCESSO", "SEM_PERMISSAO") else 1


if __name__ == "__main__":
    sys.exit(main())
