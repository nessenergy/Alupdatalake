#!/usr/bin/env bash
# Deploy do AlupData dentro do Cloud Build (ADR 030): tradução, sem mudança de comportamento, do job `terraform`
# de .github/workflows/deploy.yml. Roda como a conta de deploy, na imagem do Cloud SDK (gcloud, bq, curl, python).
set -euo pipefail

UV_VERSAO="0.5.11"
TERRAFORM_VERSAO="1.15.8"

# Valida antes de qualquer efeito colateral.
[[ "${AMBIENTE:-}" =~ ^(dev|hml|prod)$ ]] || { echo "AMBIENTE inválido: '${AMBIENTE:-}' (dev, hml ou prod)."; exit 1; }
[[ "${MODULO:-}" =~ ^(all|infra|connectors)$ ]] || { echo "MODULO inválido: '${MODULO:-}' (all, infra ou connectors)."; exit 1; }

if [ "$MODULO" = "connectors" ]; then
  echo "módulo connectors: só a imagem é construída (passo anterior); sem Terraform."
  exit 0
fi

if [ "$MODULO" = "all" ]; then
  TAG="${COMMIT_SHA:-}"
else
  TAG="${IMAGEM_SHA:-}"
fi
if [[ ! "$TAG" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Informe o SHA completo de uma imagem já publicada."
  exit 1
fi
IMAGEM="$IMAGEM_BASE:$TAG"

# A conta de deploy é a conta com que o build roda.
CONTA_DEPLOY="$(gcloud config get-value account 2>/dev/null)"
[ -n "$CONTA_DEPLOY" ] || { echo "Não foi possível descobrir a conta de deploy do build."; exit 1; }

# Falha antes do init/plan se a imagem não existe no ambiente escolhido.
# `images describe` exige containeranalysis.occurrences.list, que a conta de deploy não tem
# (e não deve ter); `images list` responde a mesma pergunta com o que ela já pode ler.
encontrada="$(gcloud artifacts docker images list "$IMAGEM_BASE" \
  --include-tags --filter="tags:$TAG" --format='value(version)')"
if [ -z "$encontrada" ]; then
  echo "Imagem $IMAGEM não existe em $AMBIENTE."
  exit 1
fi

# Ferramentas, versões fixadas como em cloudbuild/ci.sh.
curl -LsSf "https://astral.sh/uv/${UV_VERSAO}/install.sh" | sh
export PATH="$HOME/.local/bin:$PATH"
curl -sSfL -o /tmp/terraform.zip \
  "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSAO}/terraform_${TERRAFORM_VERSAO}_linux_amd64.zip"
python3 -m zipfile -e /tmp/terraform.zip /tmp/terraform-bin
install -m 0755 /tmp/terraform-bin/terraform /usr/local/bin/terraform

cd infra
# State no bucket do próprio projeto, criado pelo bootstrap.
terraform init -backend-config="bucket=$TF_ESTADO"
terraform plan -var-file="environments/$AMBIENTE.tfvars" \
  -var="imagem_ingestao=$IMAGEM" \
  -var="deploy_service_account=$CONTA_DEPLOY" \
  -var="dataform_git_token_versao=$DATAFORM_TOKEN_VERSAO" \
  -out=tfplan
terraform apply tfplan

# Liga o TABLE_STORAGE do projeto. Idempotente; exige bigquery.config.update (bootstrap).
PROJETO_TF="$(terraform output -raw project_id)"
REGIAO_TF="$(terraform output -raw region)"
bq query --use_legacy_sql=false --project_id="$PROJETO_TF" \
  "ALTER PROJECT \`$PROJETO_TF\` SET OPTIONS (\`region-$REGIAO_TF.enable_info_schema_storage\` = TRUE)"

SA_DATAFORM="$(terraform output -raw service_account_dataform)"
REPO_DATAFORM="$(terraform output -raw repositorio_dataform)"
cd ..

uv sync --frozen --no-dev

# Bronze, Silver e Gold vêm do Dataform (ADR 012). Projeto e região saem do state, e não do padrão da
# configuração, para que um deploy de prod não caia em dev.
if [ -z "$REPO_DATAFORM" ]; then
  echo "Repositorio Dataform ainda nao existe: grave o token do GitHub no secret alupdata-dataform-git-token e defina _DATAFORM_TOKEN_VERSAO no gatilho (docs/runbook/primeiro-deploy.md), depois reexecute o deploy."
  exit 1
fi
GCP_PROJECT_ID="$PROJETO_TF" GCP_REGION="$REGIAO_TF" \
  uv run python -m scripts.executar_dataform --service-account "$SA_DATAFORM" --repositorio "$REPO_DATAFORM"

# Domínio, responsável e origem de cada Gold no Knowledge Catalog (ADR 014), depois do Dataform.
uv run python -m scripts.anotar_catalogo --projeto "$PROJETO_TF" --regiao "$REGIAO_TF"
