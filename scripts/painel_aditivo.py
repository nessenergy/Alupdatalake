"""Gera o `dados-aditivo.json` da tela do Aditivo 01 (painel/aditivo.html).

Fonte única: `painel/aditivo.toml`, editado à mão junto com
`docs/contrato/aditivo-01-conjuntos-publicos.md`. Sem BigQuery, sem GitHub —
o estado de cada item já é conhecido no momento em que o PR que o entrega é
mesclado; não há por que reconsultar a origem a cada hora.

    uv run python -m scripts.painel_aditivo --saida dados-aditivo.json
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Brasília não tem horário de verão desde 2019 (mesmo motivo de scripts/painel.py).
BRASILIA = timezone(timedelta(hours=-3))
ADITIVO = Path(__file__).resolve().parents[1] / "painel" / "aditivo.toml"
ESTADOS = {"entregue", "pendente", "revisao"}


def carregar(caminho: Path = ADITIVO) -> dict[str, Any]:
    """Lê e valida o arquivo; erro diz o item e o que está errado."""
    dados = tomllib.loads(caminho.read_text(encoding="utf-8"))
    vistos: set[int] = set()
    for grupo in dados["grupo"]:
        for item in grupo["item"]:
            numero = item["numero"]
            if numero in vistos:
                raise ValueError(f"item {numero}: número repetido")
            vistos.add(numero)
            if item["estado"] not in ESTADOS:
                raise ValueError(f"item {numero}: estado {item['estado']!r} fora de {sorted(ESTADOS)}")
            if item["estado"] == "entregue" and not (item.get("entregue_em") and item.get("prs")):
                raise ValueError(f"item {numero}: entregue exige entregue_em e prs")
            if item["estado"] == "revisao" and not item.get("nota"):
                raise ValueError(f"item {numero}: revisao exige nota")
    esperados = set(range(1, max(vistos) + 1))
    faltando = esperados - vistos
    if faltando:
        raise ValueError(f"itens faltando na sequência 1..{max(vistos)}: {sorted(faltando)}")
    return dados


def _datas(valor: Any) -> Any:
    if isinstance(valor, dict):
        return {k: _datas(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_datas(v) for v in valor]
    if isinstance(valor, date):
        return valor.isoformat()
    return valor


def montar(dados: dict[str, Any], agora: datetime) -> dict[str, Any]:
    """Subtotal item a item: só `entregue` e `pendente` contam — `revisao` fica de fora,
    porque a estimativa ainda não é a que vale (ver a nota do próprio item)."""
    itens = [i for g in dados["grupo"] for i in g["item"]]
    no_subtotal = [i for i in itens if i["estado"] != "revisao"]
    estimado = sum(i["horas"] for i in no_subtotal)
    apontado = sum(i["horas"] for i in no_subtotal if i["estado"] == "entregue")
    entregues = sum(1 for i in no_subtotal if i["estado"] == "entregue")
    return {
        "gerado_em": agora.isoformat(),
        "titulo": dados["titulo"],
        "pedido_em": dados["pedido_em"].isoformat(),
        "issue": dados["issue"],
        "documento": dados["documento"],
        "subtotal": {
            "estimado": estimado,
            "apontado": apontado,
            "itens_total": len(no_subtotal),
            "itens_entregues": entregues,
        },
        "grupos": _datas(dados["grupo"]),
    }


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - E/S
    parser = argparse.ArgumentParser(description="Gera o dados-aditivo.json da tela do Aditivo 01")
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args(argv)

    dados = carregar()
    saida = montar(dados, datetime.now(BRASILIA))
    args.saida.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    s = saida["subtotal"]
    print(f"painel-aditivo: {s['itens_entregues']}/{s['itens_total']} itens -> {args.saida}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
