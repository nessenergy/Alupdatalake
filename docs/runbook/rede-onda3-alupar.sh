#!/usr/bin/env bash
# Rede das fontes internas do AlupData (ADR 024): a parte GCP da Alupar,
# passos 0, G1 a G6 do docs/runbook/rede-onda3.md, no projeto alupar-networking.
#
# Roda no Cloud Shell, com conta administradora da organização alupar.com.br.
# Não é código do nosso infra/: a rede é da Alupar. Aplicado em 25/09/2026 pela
# conta ness@alupar.com.br, a pedido e com acompanhamento da Alupar.
#
#   bash rede-onda3-alupar.sh                    -> só mostra o que faria
#   APLICAR=1 bash rede-onda3-alupar.sh          -> aplica
#   REDE_FMB=a.b.c.d/nn APLICAR=1 bash ...       -> aplica e cria a rota até o FMB (G6)
#
# Idempotente: o que já existe é pulado. prod-alupdata entra nas duas listas
# abaixo depois do bootstrap de produção; antes disso, o agente do Cloud Run de
# prod não existe e o G3 falha ("Service account ... does not exist").
set -euo pipefail
export CLOUDSDK_CORE_DISABLE_PROMPTS=1 # sem pergunta escondida: API desligada vira "não", não trava
HOST=alupar-networking; VPC=vpc-dr-prd; REG=us-central1
SUB=snet-vpc-dr-prd-us-central1-alupdata; FAIXA=172.16.9.0/26
PROJS="alupar-dev-alupdata alupar-hm-alupdata"
NUMS="674823725603 3658282685"
GRUPO="group:operacao-datalake@ness.com.br"
LEITURA="roles/compute.networkViewer roles/dns.reader"
run() { echo "+ $*" >&2; if [ "${APLICAR:-0}" = 1 ]; then "$@"; fi; }
titulo() { echo; echo "===== $1"; }

titulo "0. Acesso da ness. em $HOST: só leitura"
for m in "$GRUPO" "user:resper@ness.com.br"; do
  for r in $(gcloud projects get-iam-policy $HOST --flatten=bindings \
             --filter="bindings.members:$m" --format="value(bindings.role)"); do
    case " $LEITURA " in *" $r "*) ;; *) run gcloud projects remove-iam-policy-binding $HOST \
      --member="$m" --role="$r" --condition=None --quiet >/dev/null ;; esac
  done
done
for r in $LEITURA; do
  run gcloud projects add-iam-policy-binding $HOST --member="$GRUPO" --role=$r --condition=None --quiet >/dev/null
done

titulo "G1. Sub-rede $SUB ($FAIXA)"
if gcloud compute networks subnets describe $SUB --region=$REG --project=$HOST >/dev/null 2>&1; then
  echo "já existe"
else
  run gcloud compute networks subnets create $SUB --project=$HOST --network=$VPC --region=$REG \
    --range=$FAIXA --enable-private-ip-google-access
fi

titulo "G3. Agentes do Cloud Run usam a sub-rede"
for n in $NUMS; do
  sa="serviceAccount:service-$n@serverless-robot-prod.iam.gserviceaccount.com"
  run gcloud compute networks subnets add-iam-policy-binding $SUB --project=$HOST --region=$REG \
    --member="$sa" --role=roles/compute.networkUser >/dev/null
  run gcloud projects add-iam-policy-binding $HOST --member="$sa" \
    --role=roles/compute.networkViewer --condition=None --quiet >/dev/null
done

titulo "G4. Exceção em compute.restrictSharedVpcSubnetworks (só nos projetos do AlupData)"
for p in $PROJS; do
  run gcloud resource-manager org-policies allow compute.restrictSharedVpcSubnetworks \
    "projects/$HOST/regions/$REG/subnetworks/$SUB" --project=$p >/dev/null
done

titulo "G5. Firewall: sub-rede do AlupData -> FortiGate, TCP 1521"
if gcloud compute firewall-rules describe vpc-dr-prd-ingress-allow-alupdata-fgt --project=$HOST >/dev/null 2>&1; then
  echo "já existe"
else
  run gcloud compute firewall-rules create vpc-dr-prd-ingress-allow-alupdata-fgt --project=$HOST \
    --network=$VPC --direction=INGRESS --priority=900 --action=ALLOW --rules=tcp:1521 \
    --source-ranges=$FAIXA --target-tags=allow-fgt
fi

titulo "G6. Rota até a rede do FMB"
if [ -z "${REDE_FMB:-}" ]; then
  echo "PULADO: informe REDE_FMB=a.b.c.d/nn (faixa da rede do Oracle FMB)"
elif gcloud compute routes describe route-alupdata-to-fmb --project=$HOST >/dev/null 2>&1; then
  echo "já existe"
else
  run gcloud compute routes create route-alupdata-to-fmb --project=$HOST --network=$VPC \
    --destination-range="$REDE_FMB" --next-hop-address=172.16.8.5 --priority=100
fi

titulo "G2. Projetos do AlupData como projetos de serviço"
for p in $PROJS; do
  if [ "$(gcloud compute shared-vpc get-host-project $p --format='value(name)' 2>/dev/null)" = "$HOST" ]; then
    echo "$p: já ligado"
  elif ! gcloud services list --enabled --project=$p --filter="config.name=compute.googleapis.com" \
         --format="value(config.name)" | grep -q compute; then
    echo "$p: PULADO - API Compute desligada; a ness. ativa pelo bootstrap e depois rode de novo"
  else
    run gcloud compute shared-vpc associated-projects add $p --host-project=$HOST
  fi
done

titulo "Conferência"
gcloud compute networks subnets describe $SUB --region=$REG --project=$HOST \
  --format="value(name,ipCidrRange,privateIpGoogleAccess)" 2>/dev/null || echo "sub-rede ainda não existe"
gcloud compute shared-vpc associated-projects list $HOST --format="value(id)"
for p in $PROJS; do echo "--- $p"; gcloud resource-manager org-policies describe \
  compute.restrictSharedVpcSubnetworks --project=$p --effective --format="yaml(listPolicy)"; done
[ "${APLICAR:-0}" = 1 ] || echo; [ "${APLICAR:-0}" = 1 ] || echo "Nada foi aplicado. Para aplicar: APLICAR=1 bash rede-onda3-alupar.sh"
