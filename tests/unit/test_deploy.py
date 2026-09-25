"""Executa as guardas do deploy sem credenciais, serviços ou provisionamento."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parents[2]
SHA = "a" * 40
BASE = "us-central1-docker.pkg.dev/example-dev/images/cli"


def workflow():
    return yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8"))


def test_deploy_has_no_composer():
    config = workflow()
    inputs = config[True]["workflow_dispatch"]["inputs"]
    assert inputs["module"]["options"] == ["all", "infra", "connectors"]
    assert inputs["image_sha"]["required"] is False
    assert "sync-dags" not in config["jobs"]


@pytest.mark.parametrize(
    ("module", "image_sha", "exists", "success"),
    [
        ("all", "", True, True),
        ("infra", SHA, True, True),
        ("infra", "", True, False),
        ("infra", "latest", True, False),
        ("infra", "a" * 7, True, False),
        ("infra", '$(touch injected);"', True, False),
        ("infra", SHA, False, False),
    ],
)
def test_deploy_image_guard(module, image_sha, exists, success, tmp_path):
    bash = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else shutil.which("bash")
    assert bash, "Bash é necessário para verificar o workflow"
    steps = workflow()["jobs"]["terraform"]["steps"]
    guard = next(step for step in steps if step.get("id") == "image")
    assert guard["env"]["IMAGE_SHA"] == "${{ inputs.image_sha }}"
    assert guard["env"]["DEPLOY_MODULE"] == "${{ inputs.module }}"
    assert "${{" not in guard["run"]
    cloud = next(step for step in steps if "gcloud artifacts docker images list" in step.get("run", ""))
    assert cloud["env"]["INGESTION_IMAGE"] == "${{ steps.image.outputs.reference }}"
    assert steps.index(guard) < next(i for i, step in enumerate(steps) if "auth@" in step.get("uses", ""))
    assert cloud["run"].index("gcloud artifacts") < cloud["run"].index("terraform init")
    # Funções substituem os executáveis; nenhuma chamada chega ao GCP ou Terraform.
    # A guarda decide pela saída, não pelo código de retorno: `images list` de
    # uma tag inexistente responde vazio e com sucesso.
    stub = """gcloud() {
  echo "gcloud $*" >> calls
  if [ "$IMAGE_EXISTS" = 0 ]; then echo "sha256:0123456789abcdef"; fi
}
terraform() { echo "terraform $*" >> calls; }
"""
    (tmp_path / "infra").mkdir()
    result = subprocess.run(  # noqa: S603
        [bash, "--noprofile", "--norc", "-e", "-o", "pipefail"],
        input=stub
        + guard["run"]
        + '\nIFS= read -r image_output < image-output\nINGESTION_IMAGE="${image_output#reference=}"\n'
        + cloud["run"],
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env={
            **os.environ,
            "DEPLOY_MODULE": module,
            "IMAGE_SHA": image_sha,
            "GITHUB_SHA": "c" * 40,
            "IMAGE_BASE": BASE,
            "GITHUB_OUTPUT": "image-output",
            "IMAGE_EXISTS": "0" if exists else "1",
            "DEPLOY_ENVIRONMENT": "dev",
        },
    )
    assert (result.returncode == 0) is success, result.stderr
    calls = (tmp_path / "calls").read_text() if (tmp_path / "calls").exists() else ""
    if success:
        expected_sha = "c" * 40 if module == "all" else image_sha
        assert f"gcloud artifacts docker images list {BASE} --include-tags" in calls
        assert f"--filter=tags:{expected_sha}" in calls
        assert f"-var=imagem_ingestao={BASE}:{expected_sha}" in (tmp_path / "infra/calls").read_text()
        assert f"reference={BASE}:{expected_sha}" in (tmp_path / "image-output").read_text()
    elif exists:
        assert not calls
    assert not (tmp_path / "injected").exists()
    if not success:
        assert not (tmp_path / "infra/calls").exists()


def test_table_storage_step():
    steps = workflow()["jobs"]["terraform"]["steps"]
    step = next(s for s in steps if s.get("name") == "Ligar o TABLE_STORAGE do projeto")
    run = step["run"]
    assert "enable_info_schema_storage" in run
    assert "= TRUE" in run
    assert "terraform output -raw project_id" in run
    assert "terraform output -raw region" in run
    assert "${{" not in run
    apply_index = next(i for i, s in enumerate(steps) if "terraform apply tfplan" in s.get("run", ""))
    dataform_index = next(i for i, s in enumerate(steps) if "scripts.executar_dataform" in s.get("run", ""))
    assert apply_index < steps.index(step) < dataform_index


def test_terraform_image_validation(tmp_path):
    terraform = shutil.which("terraform")
    if not terraform:
        pytest.skip("Terraform é verificado também pelo job de infraestrutura")
    source = (ROOT / "infra/variables.tf").read_text(encoding="utf-8")
    start = source.index('variable "imagem_ingestao" {')
    block = source[start : source.index("\n}", start) + 2]
    (tmp_path / "main.tf").write_text(block, encoding="utf-8")
    cases = ["", f"{BASE}:{SHA}", f"{BASE}@sha256:{'b' * 64}", f"{BASE}:latest", f"{BASE}:abcdef0"]
    tests = []
    for index, value in enumerate(cases):
        expected = "expect_failures = [var.imagem_ingestao]" if index >= 3 else ""
        tests.append(
            f'run "case_{index}" {{\ncommand = plan\nvariables {{ imagem_ingestao = "{value}" }}\n{expected}\n}}'
        )
    (tmp_path / "image.tftest.hcl").write_text("\n".join(tests), encoding="utf-8")
    for command in (["init", "-backend=false"], ["test", "-no-color"]):
        result = subprocess.run([terraform, *command], cwd=tmp_path, capture_output=True, text=True)  # noqa: S603
        assert result.returncode == 0, result.stdout + result.stderr
