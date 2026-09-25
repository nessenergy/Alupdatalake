"""Workflow que roda o `teste-conexao-<fonte>` (ADR 024).

Pessoa não tem `run.jobs.run` (ADR 015): é o mesmo caminho auditável do
*Executar ingestão*, pela SA de deploy, com o GitHub registrando quem testou
qual fonte em qual ambiente.
"""

import re
from pathlib import Path

from tests.unit.test_executar_ingestao import _blocos_run

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "testar-conexao.yml"


def _texto() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_so_roda_a_mao_com_ambiente_e_fonte():
    texto = _texto()
    assert re.search(r"^on:\s*\n\s+workflow_dispatch:", texto, re.MULTILINE)
    for gatilho in ("push:", "pull_request", "schedule:"):
        assert gatilho not in texto, gatilho
    for entrada in ("environment:", "fonte:"):
        assert re.search(rf"^\s{{6}}{entrada}", texto, re.MULTILINE), entrada


def test_permissoes_minimas_wif_e_ambiente_do_github():
    texto = _texto()
    assert re.search(r"^permissions:\s*\n\s+contents: read\s*\n\s+id-token: write\s*$", texto, re.MULTILINE)
    assert "environment: ${{ inputs.environment }}" in texto
    assert "workload_identity_provider: ${{ vars.GCP_WIF_PROVIDER }}" in texto
    assert "service_account: ${{ vars.GCP_DEPLOY_SA }}" in texto


def test_entrada_valida_antes_e_nunca_vai_direto_para_o_shell():
    blocos = _blocos_run(_texto())
    for bloco in blocos:
        assert "${{ inputs." not in bloco, bloco
    script = "\n".join(blocos)
    # Mesmo formato da variável `fontes_teste_conexao`: o nome do secret alupdata-<fonte>-dsn.
    assert "^[a-z0-9-]+$" in script
    assert script.index("^[a-z0-9-]+$") < script.index("gcloud run jobs execute")


def test_executa_so_o_job_de_teste_e_espera():
    script = "\n".join(_blocos_run(_texto()))
    assert 'JOB="teste-conexao-$FONTE"' in script
    assert "gcloud run jobs execute" in script
    assert "--wait" in script
    assert "--args" not in script, "o job já sabe o que testar; nada de argumento vindo de fora"
