# Skills do projeto

> Estes arquivos são Markdown com frontmatter, sem runtime. O Claude Code os
> carrega automaticamente; outros agentes (Codex, Cursor, Gemini, Cline) leem o
> índice em [`AGENTS.md`](../../AGENTS.md) e abrem o `SKILL.md` pelo caminho.

Skills carregadas automaticamente por agentes que trabalham neste repositório.
Cada uma cobre um eixo da Fase 1 e aponta para os documentos que já existem em
`docs/` — elas complementam o contrato e a arquitetura, não os substituem.

| Skill | Quando dispara |
|---|---|
| `conector-alupdata` | adicionar/alterar uma fonte de dados — os 7 componentes da cláusula 2ª |
| `gcp-alupdata` | BigQuery, GCS, Secret Manager, Composer/Scheduler, Terraform |
| `ssdlc-alupdata` | credenciais, dependências, Bandit/pip-audit/Gitleaks — cláusula 8ª |
| `homologacao-onda` | fechar onda, medição, dependências pendentes da Alup |

## Skills do Google (vendorizadas)

`google/` traz uma shortlist de <https://github.com/google/skills> (Apache 2.0),
copiada por `uv run python -m scripts.sync_skills_google`:

| Skill | Para quê |
|---|---|
| `bigquery-basics` | mecânica do produto BigQuery |
| `google-cloud-storage-basics` | camada raw no GCS |
| `gcloud` | guardrails da CLI |
| `cloud-run-basics` | orquestração das Ondas 1–2 (ADR 004) |
| `google-cloud-waf-cost-optimization` | custo de infra é da contratante (cláusula 5ª) |
| `datalineage-bigquery-asset-impact-analysis` | o que quebra a jusante se uma tabela mudar — linhagem das ADRs 013 e 014 |

**Precedência**: as do Google ensinam o produto; as do projeto dizem como *este
contrato* usa o produto. Onde conflitarem — nomenclatura, particionamento,
segredos, o que vai em cada camada — **vale a do projeto**. Não edite os
arquivos em `google/`: a próxima sincronização sobrescreve.

Outras entram acrescentando o nome à `SHORTLIST` em
`scripts/sync_skills_google.py` — `iam-helper-*` na Onda 4, por exemplo.
`managed-airflow-dag-authoring` saiu do horizonte: a Onda 3 orquestra em Cloud
Workflows (ADR 017).

> **A `bigquery-basics` pede prefixo de atribuição em todo comando `gcloud`**
> desde a revisão `2a1e454`. Neste projeto ele **não** se aplica — ver
> `gcp-alupdata`, que tem precedência.

## Skills da HashiCorp e do GitHub (vendorizadas)

| Pasta | Skill | Para quê |
|---|---|---|
| `hashicorp/` | `terraform-style-guide` | estilo de HCL — com nomes em português, como o projeto já faz |
| `hashicorp/` | `terraform-test` | `terraform test`, **só em `plan` ou com provider simulado** |
| `github/` | `github-actions-hardening` | revisão de segurança dos workflows — o deploy assume a SA do GCP (cláusula 8ª) |

Origem, revisão, licença e divergências no `UPSTREAM.md` de cada pasta. Mesma
regra: não edite os arquivos copiados; ajuste a skill do projeto.

Para editar, altere o `SKILL.md` da pasta correspondente. O bloco `description`
do frontmatter é o que decide se a skill é acionada — descreva **quando** usar,
com os termos que aparecem no dia a dia do projeto.
