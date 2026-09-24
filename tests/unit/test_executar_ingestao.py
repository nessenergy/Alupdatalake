"""Workflow que dispara um Cloud Run Job de ingestão à mão.

Só a SA de deploy tem `run.jobs.run` (ADR 015): pessoa não executa job. O
workflow é o caminho auditável para isso — fica registrado no GitHub quem
disparou, qual conector e com que janela.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
WORKFLOW = RAIZ / ".github" / "workflows" / "executar-ingestao.yml"


def _texto() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _blocos_run(texto: str) -> list[str]:
    """Conteúdo de cada `run:`, inline ou em bloco `|`."""
    blocos, linhas = [], texto.splitlines()
    for i, linha in enumerate(linhas):
        achado = re.match(r"^(\s*)(?:- )?run:\s*(.*)$", linha)
        if not achado:
            continue
        recuo, resto = len(achado.group(1)), achado.group(2)
        if resto not in ("|", ">"):
            blocos.append(resto)
            continue
        corpo = []
        for seguinte in linhas[i + 1 :]:
            if seguinte.strip() and len(seguinte) - len(seguinte.lstrip()) <= recuo:
                break
            corpo.append(seguinte)
        blocos.append("\n".join(corpo))
    return blocos


def test_so_roda_por_disparo_manual_com_as_entradas_da_janela():
    texto = _texto()
    assert re.search(r"^on:\s*\n\s+workflow_dispatch:", texto, re.MULTILINE)
    for gatilho in ("push:", "pull_request", "schedule:"):
        assert gatilho not in texto, gatilho
    for entrada in ("environment:", "conector:", "de:", "ate:", "uri:"):
        assert re.search(rf"^\s{{6}}{entrada}", texto, re.MULTILINE), entrada
    for ambiente in ("dev", "hml", "prod"):
        assert re.search(rf"^\s+- {ambiente}$", texto, re.MULTILINE), ambiente


def test_permissoes_minimas_e_ambiente_do_github():
    texto = _texto()
    assert re.search(r"^permissions:\s*\n\s+contents: read\s*\n\s+id-token: write\s*$", texto, re.MULTILINE)
    assert "environment: ${{ inputs.environment }}" in texto


def test_entrada_do_usuario_nunca_vai_direto_para_o_shell():
    """`${{ inputs.x }}` dentro de `run:` é colado no script antes de o shell rodar."""
    for bloco in _blocos_run(_texto()):
        assert "${{ inputs." not in bloco, bloco


def test_valida_conector_e_datas_antes_de_chamar_o_gcp():
    script = "\n".join(_blocos_run(_texto()))
    assert "^[a-z0-9_]+$" in script
    assert "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" in script
    assert "^gs://" in script
    assert script.index("[a-z0-9_]") < script.index("gcloud run jobs execute")


def test_executa_o_job_e_espera_o_resultado():
    script = "\n".join(_blocos_run(_texto()))
    assert "gcloud run jobs execute" in script
    assert "--wait" in script
    assert "reprocessar-raw" in script
    assert "ingerir" in script


def test_autentica_por_wif_com_a_sa_de_deploy():
    texto = _texto()
    assert "workload_identity_provider: ${{ vars.GCP_WIF_PROVIDER }}" in texto
    assert "service_account: ${{ vars.GCP_DEPLOY_SA }}" in texto
    assert "credentials_json" not in texto
