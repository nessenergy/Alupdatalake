"""Toda ação dos workflows fixada por SHA de commit, com a versão ao lado.

Tag como `@v2` é mutável: quem controla o repositório da ação pode apontá-la
para outro código, e esse código roda com o token do job. No workflow de
deploy, esse token assume a SA de deploy no GCP da contratante por Workload
Identity Federation (ADR 015) — é a credencial mais sensível do projeto.

SHA fixo sem atualização envelhece, por isso o Dependabot mantém as ações; e
por isso este teste cobra os dois lados.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
WORKFLOWS = sorted((RAIZ / ".github" / "workflows").glob("*.yml"))
FIXADA = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40} # v\d+\.\d+\.\d+$")


def referencias() -> list[tuple[str, str]]:
    saida = []
    for workflow in WORKFLOWS:
        for linha in workflow.read_text(encoding="utf-8").splitlines():
            if (achado := re.search(r"uses:\s*(.+?)\s*$", linha)) is None:
                continue
            valor = achado.group(1).strip().strip('"')
            if not valor.startswith("./"):  # ação local vem do próprio commit
                saida.append((workflow.name, valor))
    return saida


def test_ha_workflow_para_conferir():
    assert referencias(), "nenhum `uses:` encontrado em .github/workflows"


def test_toda_acao_esta_fixada_por_sha_com_a_versao_ao_lado():
    soltas = [f"{nome}: {valor}" for nome, valor in referencias() if not FIXADA.match(valor)]

    assert not soltas, "ação sem SHA de 40 caracteres e `# vX.Y.Z` ao lado:\n" + "\n".join(soltas)


def test_o_dependabot_mantem_as_acoes():
    """SHA fixo sem quem o atualize vira ação velha com falha conhecida."""
    config = (RAIZ / ".github" / "dependabot.yml").read_text(encoding="utf-8")

    assert "package-ecosystem: github-actions" in config
