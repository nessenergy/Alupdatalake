"""F0 do plano de FinOps: custo que chega na fatura sem rótulo não se atribui.

A conta do GCP é da Alup (cláusula 5ª) e o teto da E2 é apertado. O painel de
custo e o orçamento por ambiente dependem de o recurso carregar `projeto` e
`ambiente`: sem isso, a linha aparece na fatura e ninguém sabe de quem é.

O plano cobrava "a verificação que barra recurso sem rótulo" desde 04/09
([issue #58](https://github.com/nessenergy/Alupdatalake/issues/58)) — é esta.
Ela olha o que está declarado, não o que está aplicado: recurso criado à mão
no console some no apply seguinte (regra 5), então o código é a fonte.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# Tipos que geram linha na fatura e aceitam rótulo no provider. Tipo que não
# aceita — Cloud Scheduler, repositório do Dataform — fica de fora porque
# exigir rótulo dele seria exigir o impossível.
TIPOS_COM_ROTULO = {
    "google_artifact_registry_repository",
    "google_bigquery_dataset",
    "google_cloud_run_v2_job",
    "google_cloud_run_v2_service",
    "google_dataplex_asset",
    "google_dataplex_aspect_type",
    "google_dataplex_lake",
    "google_dataplex_zone",
    "google_secret_manager_secret",
    "google_storage_bucket",
    "google_workflows_workflow",
}

OBRIGATORIOS = ("projeto", "ambiente")


def blocos_de_recurso() -> list[tuple[Path, str, str, str]]:
    """Cada recurso declarado em `infra/`, com o corpo do bloco."""
    encontrados = []
    for caminho in sorted(RAIZ.glob("infra/**/*.tf")):
        if ".terraform" in caminho.parts:
            continue
        texto = caminho.read_text(encoding="utf-8")
        for tipo, nome, corpo in re.findall(r'resource "(\w+)" "(\w+)" \{\n((?:.|\n)*?)\n\}', texto):
            encontrados.append((caminho, tipo, nome, corpo))
    return encontrados


def test_ha_recurso_para_conferir():
    assert blocos_de_recurso(), "nenhum recurso encontrado em infra/"


def test_todo_recurso_faturavel_carrega_a_taxonomia_de_custo():
    sem_rotulo = []
    for caminho, tipo, nome, corpo in blocos_de_recurso():
        if tipo not in TIPOS_COM_ROTULO:
            continue
        if "labels" not in corpo or any(chave not in corpo for chave in OBRIGATORIOS):
            sem_rotulo.append(f"{caminho.relative_to(RAIZ)}: {tipo}.{nome}")

    assert not sem_rotulo, "recurso faturável sem `projeto` e `ambiente` nos rótulos:\n" + "\n".join(sem_rotulo)
