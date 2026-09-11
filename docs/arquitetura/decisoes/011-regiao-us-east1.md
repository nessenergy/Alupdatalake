# ADR 011 — Região do ambiente: `us-east1`

**Status**: aceito · **Data**: 2026-09-10 · **Substitui** a [ADR 009](009-regiao-do-ambiente.md)

## Contexto

A ADR 009 fixou `southamerica-east1` com base em três eixos — residência de
dado, latência às origens e custo — e deixou uma ressalva: se a decisão
mudasse, a mudança chegaria antes do primeiro `terraform apply`, enquanto ainda
não custa nada.

É o que acontece. A revisão arquitetural enviada ao Google em 04/09 (pendência
G1, [issue #77](https://github.com/nessenergy/Alupdatalake/issues/77)) foi
discutida em reunião com o Google, e a decisão que saiu dela é manter o ambiente
nos **Estados Unidos**. O `apply` segue bloqueado por A3, então nenhum dataset,
bucket ou repositório de imagem existe ainda em região alguma: trocar agora é
editar variável, não migrar dado.

Os projetos ficam na organização GCP da Alupar e são vinculados à conta de
faturamento da Alup (E1 e E2, esclarecidos em 09/09). A ness. desenvolve a
plataforma; a operação e o custo são da Alup.

## Decisão

Todo o ambiente — datasets Bronze/Silver/Gold, bucket raw, Cloud Run Jobs,
Scheduler, secrets, Artifact Registry, repositório Dataform (ADR 012), lake do
Knowledge Catalog (ADR 014) e, na Onda 3, o ambiente Airflow — fica em
**`us-east1`** (Carolina do Sul), em `dev` e em `prod`. O valor passa a ser o
padrão de `variable "region"`.

### Por que `us-east1` entre as regiões americanas

- **Latência às origens.** As fontes internas da Onda 3 estão no Brasil e são
  lidas pela VPN em lotes de `banco_lote` linhas (ADR 008): cada lote paga uma
  ida e volta. `us-east1` é a região americana mais próxima de São Paulo.
- **Paridade de serviço.** Dataform e Knowledge Catalog, incluindo linhagem de
  dado, constam na documentação de localização do Google para `us-east1`
  (conferido em 10/09).
- **Preço.** Mesma faixa de `us-central1`, e abaixo de `southamerica-east1`.
- **Simplicidade.** Uma região para tudo continua sendo uma variável só no
  Terraform.

### Alternativas descartadas

- **`us-central1`**: região padrão do Google, onde recurso novo costuma chegar
  primeiro, mas mais distante das origens brasileiras. Não há serviço do projeto
  que exista lá e falte em `us-east1`.
- **Multirregião `US`**: não entrega recuperação de desastre sem replicação
  configurada à parte; *scans* de qualidade e de *profiling* do Knowledge
  Catalog não são suportados em localização multirregião; e Cloud Run,
  Scheduler e Airflow são regionais de qualquer forma, o que deixaria o
  ambiente com duas localizações para manter.

## Consequências

- **A escolha é praticamente irreversível depois do primeiro `apply`** — dataset
  do BigQuery não muda de região. Mudar depois é migração de dado, com ADR
  próprio, exatamente como a ADR 009 descrevia para a região anterior.
- **O custo unitário cai** em relação a `southamerica-east1`. O painel de custo
  (ADR 007) mostra o efeito desde o primeiro mês.
- **Transferência internacional de dado pessoal (LGPD, art. 33) — aceita, não
  bloqueia o `apply`.** A maior parte do dado é de mercado e de operação; o dado
  pessoal previsto está no Hubspot (dono e nome livre dos negócios, A9 —
  contatos não são lidos) e possivelmente no Portal Alup. A transferência fica documentada em três peças, em `docs/lgpd/`:
  - **DPA** — o *Cloud Data Processing Addendum* do Google, aceito pela Alupar
    no contrato de nuvem;
  - **RoPA** — registro das operações de tratamento (art. 37);
  - **RIPD/DPIA** — relatório de impacto (art. 38).

  RoPA e RIPD são documentos da controladora: a ness. entrega a minuta técnica
  (quais dados, onde ficam, quem acessa, fluxo e linhagem) e a Alup assume e
  assina. A minuta registra que o acesso da ness. a dado pessoal real fica
  restrito ao período de desenvolvimento e homologação.
- **Verificações antes do primeiro `apply`:**
  1. a organização da Alupar não tem a restrição `gcp.resourceLocations`
     limitando recursos ao Brasil — se tiver, o `apply` falha;
  2. a localização dos recursos de IA generativa do Knowledge Catalog, que a
     página de localizações não informa (ADR 014).
- **O que muda no repositório** (PR de infraestrutura, antes do `apply`): o
  padrão de `infra/variables.tf`, os dois `.tfvars`, o padrão de `gcp_region` em
  `src/core/config.py`, as expectativas de `tests/unit/test_sql.py`, o runbook
  de deploy e a skill de convenções de GCP. `sql/gold/custo_consultas.sql` já
  recebe a região por parâmetro; as tarifas-premissa dele e de
  `src/portal/custo.py` (US$ 6,25 por TiB varrido, US$ 0,020 por GiB·mês) são
  conferidas contra a tabela de preço de `us-east1` no mesmo PR. Os relatórios
  já emitidos não mudam: registram o que valia na data deles.
- A pergunta **E7** do Questionário de Gaps fica respondida por esta ADR.
