# Skills do projeto

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

**Precedência**: as do Google ensinam o produto; as do projeto dizem como *este
contrato* usa o produto. Onde conflitarem — nomenclatura, particionamento,
segredos, o que vai em cada camada — **vale a do projeto**. Não edite os
arquivos em `google/`: a próxima sincronização sobrescreve.

Skills de ondas futuras (`managed-airflow-dag-authoring` na Onda 3,
`datalineage-*` e `iam-helper-*` na Onda 4) entram acrescentando o nome à
`SHORTLIST` em `scripts/sync_skills_google.py`.

Para editar, altere o `SKILL.md` da pasta correspondente. O bloco `description`
do frontmatter é o que decide se a skill é acionada — descreva **quando** usar,
com os termos que aparecem no dia a dia do projeto.
