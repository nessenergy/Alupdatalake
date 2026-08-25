"""Sincroniza a shortlist de skills do Google (google/skills) para `.claude/skills/google/`.

As skills do Google ensinam os produtos (BigQuery, GCS, Cloud Run); as skills
do projeto dizem como *este contrato* usa esses produtos. Em conflito, vence a
do projeto — ver `.claude/skills/README.md`.

    uv run python -m scripts.sync_skills_google            # sincroniza a shortlist
    uv run python -m scripts.sync_skills_google --listar   # mostra o que está fixado

Licença upstream: Apache 2.0 (preservada em `.claude/skills/google/LICENSE`).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess  # noqa: S404 — chamadas com lista fixa, sem shell
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / ".claude" / "skills" / "google"
UPSTREAM = "https://github.com/google/skills"

# Shortlist deliberada: o que a Fase 1 usa hoje. Ampliar quando a onda pedir
# (managed-airflow-dag-authoring na Onda 3; datalineage-* na Onda 4).
SHORTLIST = (
    "bigquery-basics",
    "google-cloud-storage-basics",
    "gcloud",
    "cloud-run-basics",
    "google-cloud-waf-cost-optimization",
)


def _git() -> str:
    """Caminho absoluto do git — evita depender do PATH em runtime."""
    caminho = shutil.which("git")
    if caminho is None:
        raise RuntimeError("git não encontrado no PATH")
    return caminho


def _run(*args: str) -> str:
    resultado = subprocess.run(  # noqa: S603 — executável resolvido, sem shell
        [_git(), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return resultado.stdout.strip()


def sincronizar() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        origem = Path(tmp) / "skills"
        print(f"clonando {UPSTREAM} …")
        _run("clone", "--depth", "1", "--quiet", UPSTREAM, str(origem))
        revisao = _run("-C", str(origem), "rev-parse", "--short", "HEAD")

        DESTINO.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem / "LICENSE", DESTINO / "LICENSE")

        for nome in SHORTLIST:
            alvo = DESTINO / nome
            fonte = origem / "skills" / "cloud" / nome
            if not fonte.is_dir():
                print(f"  AUSENTE no upstream: {nome}")
                continue
            shutil.rmtree(alvo, ignore_errors=True)
            shutil.copytree(fonte, alvo)
            print(f"  {nome}")

        (DESTINO / "UPSTREAM.md").write_text(
            "# Origem\n\n"
            f"Skills copiadas de <{UPSTREAM}> (`skills/cloud/`), licença Apache 2.0.\n\n"
            f"Revisão sincronizada: `{revisao}`\n\n"
            "Não edite estes arquivos à mão — a próxima sincronização sobrescreve.\n"
            "Para ajustar comportamento, altere a skill do projeto correspondente\n"
            "(`gcp-alupdata`, `conector-alupdata`), que tem precedência.\n\n"
            "Atualizar: `uv run python -m scripts.sync_skills_google`\n\n"
            "## Shortlist\n\n" + "".join(f"- `{n}`\n" for n in SHORTLIST),
            encoding="utf-8",
        )
        print(f"\nrevisão {revisao} → {DESTINO.relative_to(RAIZ)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sincroniza skills do Google para o repositório")
    parser.add_argument("--listar", action="store_true", help="mostra a shortlist e sai")
    args = parser.parse_args(argv)

    if args.listar:
        for nome in SHORTLIST:
            print(nome)
        return 0
    return sincronizar()


if __name__ == "__main__":
    sys.exit(main())
