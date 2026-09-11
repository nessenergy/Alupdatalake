"""Invariantes do bootstrap de cada projeto (ADR 015, revisão de 11/09).

`infra/bootstrap/` é a raiz Terraform que a ness. aplica uma vez por projeto,
com state local, antes do primeiro deploy: APIs, bucket de state, Artifact
Registry, Workload Identity Federation e a conta de serviço de deploy. Como o
restante de `infra/`, é verificado por leitura de texto, sem projeto GCP.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).parents[2]
BOOTSTRAP = RAIZ / "infra" / "bootstrap"
AMBIENTES = ("dev", "hml", "prod")


def _ler(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8")


def _codigo() -> str:
    """Todo o código `.tf` do bootstrap, sem os `.tfvars`."""
    return "\n".join(_ler(c) for c in sorted(BOOTSTRAP.glob("*.tf")))


def _tem(padrao: str, texto: str) -> bool:
    """Regex tolerante ao alinhamento que o `terraform fmt` impõe."""
    return re.search(padrao, texto) is not None


def _bloco(texto: str, cabecalho: str) -> str:
    """Bloco HCL de nível superior que começa em `cabecalho`."""
    inicio = texto.index(cabecalho)
    return texto[inicio : texto.index("\n}\n", inicio)]


def _lista(texto: str, nome: str) -> set[str]:
    """Strings de uma lista HCL `nome = [ ... ]`."""
    corpo = re.search(rf"\b{nome}\s*=\s*\[(.*?)\]", texto, re.DOTALL)
    assert corpo, nome
    return set(re.findall(r'"([^"]+)"', corpo.group(1)))


def _infra_principal() -> list[tuple[Path, str]]:
    """Código do `infra/` que o deploy aplica — sem o bootstrap."""
    return [
        (caminho, _ler(caminho))
        for caminho in (RAIZ / "infra").rglob("*.tf")
        if ".terraform" not in caminho.parts and "bootstrap" not in caminho.parts
    ]


# ------------------------------------------------------------------ raiz


def test_bootstrap_e_raiz_separada_com_state_local() -> None:
    """Aplicado pela ness. antes de existir o bucket de state: não há backend remoto."""
    for arquivo in ("main.tf", "variables.tf", "outputs.tf"):
        assert (BOOTSTRAP / arquivo).is_file(), arquivo

    codigo = _codigo()
    assert "backend " not in codigo
    assert _tem(r'required_version\s*=\s*">= 1\.5"', codigo)
    assert _tem(r'source\s*=\s*"hashicorp/google"', codigo)


def test_bootstrap_tem_tfvars_dos_tres_ambientes_sem_valor_real() -> None:
    variaveis = _ler(BOOTSTRAP / "variables.tf")
    assert _tem(r'contains\(\["dev", "hml", "prod"\], var\.environment\)', variaveis)

    for ambiente in AMBIENTES:
        tfvars = _ler(BOOTSTRAP / "environments" / f"{ambiente}.tfvars")
        assert _tem(rf'environment\s*=\s*"{ambiente}"', tfvars), ambiente
        assert _tem(r'region\s*=\s*"us-east1"', tfvars), ambiente
        # Nenhum e-mail, host ou identificador de infraestrutura da Alup.
        assert "@" not in tfvars, ambiente
        assert not re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", tfvars), ambiente


# ------------------------------------------------------------------ APIs


APIS_ESPERADAS = {
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "billingbudgets.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "dataform.googleapis.com",
    "datalineage.googleapis.com",
    "dataplex.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "iap.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "sts.googleapis.com",
}


def test_bootstrap_habilita_as_apis_do_infra() -> None:
    codigo = _codigo()
    apis = _lista(codigo, "apis")
    assert apis >= APIS_ESPERADAS, APIS_ESPERADAS - apis

    servico = _bloco(codigo, 'resource "google_project_service" "api"')
    assert _tem(r"for_each\s*=\s*toset\(local\.apis\)", servico)
    # Tirar uma API da lista não pode derrubar o que já roda no projeto.
    assert _tem(r"disable_on_destroy\s*=\s*false", servico)


def test_toda_api_que_o_infra_referencia_e_habilitada_no_bootstrap() -> None:
    """Pega a API esquecida antes do primeiro apply, e não por um 403 no meio dele."""
    apis = _lista(_codigo(), "apis")
    for caminho, texto in _infra_principal():
        for api in re.findall(r"([a-z0-9]+\.googleapis\.com)", texto):
            assert api in apis, (caminho, api)


# ------------------------------------------------------------------ state


def test_bucket_de_state_em_us_east1_versionado_e_fechado() -> None:
    """ADR 011: tudo em `us-east1`; o state guarda o histórico do ambiente."""
    assert _tem(
        r'variable "region" \{[^}]*default\s*=\s*"us-east1"',
        _ler(BOOTSTRAP / "variables.tf"),
    )

    bucket = _bloco(_codigo(), 'resource "google_storage_bucket" "state"')
    assert _tem(r"location\s*=\s*var\.region", bucket)
    assert _tem(r"uniform_bucket_level_access\s*=\s*true", bucket)
    assert _tem(r'public_access_prevention\s*=\s*"enforced"', bucket)
    assert _tem(r"versioning\s*\{\s*enabled\s*=\s*true", bucket)
    assert not _tem(r"force_destroy\s*=\s*true", bucket)


def test_artifact_registry_docker_na_regiao_com_limpeza() -> None:
    """Custo (E2): imagem antiga não fica acumulando armazenamento pago."""
    repositorio = _bloco(_codigo(), 'resource "google_artifact_registry_repository" "imagens"')
    assert _tem(r'format\s*=\s*"DOCKER"', repositorio)
    assert _tem(r"location\s*=\s*var\.region", repositorio)
    assert "cleanup_policies" in repositorio
    assert _tem(r'action\s*=\s*"KEEP"', repositorio)
    assert "most_recent_versions" in repositorio


# ------------------------------------------------------------------ WIF


def test_wif_aceita_so_o_repositorio_do_projeto() -> None:
    codigo = _codigo()
    assert _tem(
        r'variable "github_repositorio" \{[^}]*default\s*=\s*"nessenergy/Alupdatalake"',
        _ler(BOOTSTRAP / "variables.tf"),
    )

    provedor = _bloco(codigo, 'resource "google_iam_workload_identity_pool_provider" "github"')
    assert _tem(r'issuer_uri\s*=\s*"https://token\.actions\.githubusercontent\.com"', provedor)
    assert _tem(r"attribute_condition\s*=\s*local\.condicao_wif", provedor)
    assert _tem(r'"attribute\.repository"\s*=\s*"assertion\.repository"', provedor)

    condicao = re.search(r"condicao_wif\s*=\s*(.+)", codigo).group(1)
    assert "assertion.repository == '${var.github_repositorio}'" in codigo
    assert "local.condicao_repositorio" in condicao

    # Quem pode personificar a SA de deploy: só identidade do repositório.
    personifica = _bloco(codigo, 'resource "google_service_account_iam_member" "github_personifica"')
    assert '"roles/iam.workloadIdentityUser"' in personifica
    assert "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}" in personifica
    assert "/attribute.repository/${var.github_repositorio}" in personifica


def test_wif_de_hml_e_prod_exige_o_ambiente_do_github() -> None:
    """Com GitHub Team, o job de prod só obtém token se rodar no ambiente `prod`."""
    codigo = _codigo()
    assert "environment:${var.environment}" in codigo
    assert _tem(r'variable "restringir_ao_ambiente_github" \{[^}]*default\s*=\s*true', _ler(BOOTSTRAP / "variables.tf"))

    # Em dev, o quadro (quadro.yml) roda sem `environment:` e usa a mesma SA.
    assert _tem(r"restringir_ao_ambiente_github\s*=\s*false", _ler(BOOTSTRAP / "environments" / "dev.tfvars"))
    for ambiente in ("hml", "prod"):
        assert "restringir_ao_ambiente_github" not in _ler(BOOTSTRAP / "environments" / f"{ambiente}.tfvars")


# ------------------------------------------------------------------ SA de deploy


def test_sa_de_deploy_sem_chave() -> None:
    """Cláusula 8.5: o deploy entra por WIF; chave JSON não existe em lugar nenhum."""
    assert 'resource "google_service_account" "deploy"' in _codigo()
    for caminho in (RAIZ / "infra").rglob("*.tf"):
        if ".terraform" in caminho.parts:
            continue
        assert "google_service_account_key" not in _ler(caminho), caminho
    for workflow in (RAIZ / ".github" / "workflows").glob("*.yml"):
        assert "credentials_json" not in _ler(workflow), workflow


# Papel que a SA de deploy precisa, por tipo de recurso declarado no `infra/`.
# O prefixo mais longo vence: `google_service_account_iam_member` cai em
# `google_service_account`, `google_bigquery_dataset_iam_member` em
# `google_bigquery_dataset`.
PAPEL_POR_RECURSO = {
    "google_service_account": "roles/iam.serviceAccountAdmin",
    "google_project_iam_": "roles/resourcemanager.projectIamAdmin",
    "google_project_service_identity": "roles/serviceusage.serviceUsageConsumer",
    "google_bigquery_dataset": "roles/bigquery.dataOwner",
    "google_storage_bucket": "roles/storage.admin",
    "google_secret_manager_secret": "roles/secretmanager.admin",
    "google_cloud_run_v2_": "roles/run.admin",
    "google_cloud_scheduler_job": "roles/cloudscheduler.admin",
    "google_dataform_": "roles/dataform.admin",
    "google_iap_": "roles/iap.admin",
    "google_monitoring_": "roles/monitoring.editor",
    "google_logging_metric": "roles/logging.configWriter",
}

# Recurso cujo papel não é concedido no projeto.
FORA_DO_PROJETO = {
    # Orçamento vive na conta de faturamento: o papel é da Alup conceder lá
    # (Billing Account Costs Manager), e só quando `billing_account` for preenchido.
    "google_billing_budget",
}


def test_sa_de_deploy_tem_papel_para_cada_recurso_do_infra() -> None:
    papeis = _lista(_codigo(), "papeis_deploy")

    for caminho, texto in _infra_principal():
        for tipo in re.findall(r'resource "(google_\w+)"', texto):
            if tipo in FORA_DO_PROJETO:
                continue
            prefixos = [p for p in PAPEL_POR_RECURSO if tipo.startswith(p)]
            assert prefixos, f"{caminho}: {tipo} sem papel mapeado para a SA de deploy"
            papel = PAPEL_POR_RECURSO[max(prefixos, key=len)]
            assert papel in papeis, (tipo, papel)

    # Cloud Run, Scheduler e Dataform executam como SAs que o próprio Terraform cria.
    assert "roles/iam.serviceAccountUser" in papeis


def test_sa_de_deploy_nao_recebe_papel_basico() -> None:
    papeis = _lista(_codigo(), "papeis_deploy")
    for basico in ("roles/owner", "roles/editor", "roles/viewer"):
        assert basico not in papeis
        assert f'"{basico}"' not in _codigo()


def test_sa_de_deploy_publica_imagem_so_no_repositorio_do_ambiente() -> None:
    codigo = _codigo()
    escrita = _bloco(codigo, 'resource "google_artifact_registry_repository_iam_member" "deploy_publica"')
    assert '"roles/artifactregistry.writer"' in escrita
    assert "google_service_account.deploy.email" in escrita
    assert "roles/artifactregistry.writer" not in _lista(codigo, "papeis_deploy")

    projeto = _bloco(codigo, 'resource "google_project_iam_member" "deploy"')
    assert _tem(r"for_each\s*=\s*toset\(local\.papeis_deploy\)", projeto)


# ------------------------------------------------------------------ saídas


def test_saidas_alimentam_as_variaveis_do_github() -> None:
    saidas = _ler(BOOTSTRAP / "outputs.tf")
    for nome in ("workload_identity_provider", "service_account_deploy", "bucket_state", "imagem_ingestao"):
        assert f'output "{nome}"' in saidas, nome
    assert "google_iam_workload_identity_pool_provider.github.name" in saidas
    assert "google_service_account.deploy.email" in saidas
