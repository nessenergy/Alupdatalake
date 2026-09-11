# ADR 009 — Região do ambiente: `southamerica-east1`

**Status**: substituído pela [ADR 011](011-regiao-us-east1.md) em 2026-09-10 ·
**Data**: 2026-09-04

## Contexto

O repositório subiu com `us-east1` em `infra/variables.tf` e nos dois
`.tfvars`, herdado do valor de exemplo. A pergunta E7 do Questionário de Gaps,
enviado à Alup em 31/08, assume `southamerica-east1` (São Paulo). A divergência
foi registrada como descoberta da S1 e como [issue #67](https://github.com/nessenergy/Alupdatalake/issues/67).

A decisão precisava sair **antes do primeiro `terraform apply`** por uma razão
técnica dura: **dataset do BigQuery não muda de região depois de criado.**
Corrigir mais tarde não é editar uma variável — é recriar dataset, tabela e
view, e recarregar todo o histórico já ingerido. O mesmo vale, em menor grau,
para o bucket raw e para o repositório do Artifact Registry.

Três eixos pesaram:

1. **Residência de dado.** O dado é operacional e de mercado do setor elétrico
   brasileiro, de seis geradoras nacionais, e o contratante é brasileiro.
   Manter o dado no país é a posição defensável sob a LGPD — não porque a lei
   exija localização, mas porque transferência internacional é um capítulo que
   simplesmente não se abre se o dado não sai.
2. **Latência às origens.** ONS, CCEE, ANEEL, BCB e IBGE são todos brasileiros,
   e as fontes internas da Onda 3 estão na infraestrutura da Alup, no Brasil.
   Ingestão a partir de São Paulo encurta o caminho em toda a Fase 1.
3. **Custo.** `southamerica-east1` é mais cara que `us-east1` — tipicamente na
   ordem de dezenas de por cento em computação e armazenamento. O custo de
   infra é da contratante (cláusula 5ª), e o volume da Fase 1 é modesto, então
   a diferença absoluta é pequena diante do risco de ter de recriar tudo.

## Decisão

Todo o ambiente — datasets Bronze/Silver/Gold, bucket raw, Cloud Run Jobs,
Scheduler, secrets e Artifact Registry — fica em **`southamerica-east1`**, em
`dev` e em `prod`.

O valor passa a ser o padrão de `variable "region"`, para que um ambiente novo
criado sem `.tfvars` explícito nasça na região certa em vez de nascer nos EUA.

## Consequências

- **A escolha é praticamente irreversível** depois do primeiro `apply`. Se
  algum dia precisar mudar, é migração de dado, não alteração de configuração,
  e merece ADR próprio.
- **O custo unitário sobe** em relação ao valor herdado. Como o custo é da
  contratante e há painel de custo por fonte e por camada, o efeito fica
  visível desde o primeiro mês em vez de aparecer numa fatura sem explicação.
- **Nem todo produto do Google tem paridade de recursos em São Paulo.** Se um
  serviço necessário à Fase 2 não existir na região, a saída é usar o serviço
  em outra região com o dado permanecendo aqui — não mover o dado.
- O runbook de deploy, os dois `.tfvars` e a skill de convenções de GCP passam
  a citar a região nova; não sobrou nenhuma ocorrência do valor antigo no
  repositório.

## Ressalva

A decisão foi tomada pela ness. em 04/09 com base na recomendação técnica já
registrada no relatório de 31/08. A **confirmação formal da Alup** continua
sendo a resposta à pergunta E7 do questionário. Se a resposta divergir, ela
chega antes do `apply` — que segue bloqueado por A3 — e ainda dá tempo de
inverter sem custo.
