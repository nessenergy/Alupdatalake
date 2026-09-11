# RoPA — Registro das Operações de Tratamento da plataforma AlupData

**Versão** 0.2 · **Data** 2026-09-11 · **Situação**: minuta técnica, para
revisão e aprovação da controladora

Registro exigido pelo art. 37 da LGPD. Minuta elaborada pela ness. no contrato
CPS-01025/2026 ([ADR 011](../arquitetura/decisoes/011-regiao-us-east1.md)). A
análise de risco está no [RIPD](ripd.md), os prazos na
[política de retenção](politica-de-retencao.md) e a transferência internacional
no [registro do DPA](dpa.md).

## Agentes

| Papel | Quem |
|---|---|
| Controladora | ACE Comercializadora Ltda., nome fantasia Alup — CNPJ 14.402.579/0001-23 |
| Encarregada | Rosimeire Miler dos Santos — privacidade@alupar.com.br |
| Operadora (desenvolvimento) | ness. Processos e Tecnologia Ltda., CNPJ 72.027.097/0001-37 — até o handoff |
| Suboperador (infraestrutura) | Google Cloud, sob o DPA do contrato de nuvem da Alupar |

## Comum a todas as operações

- **Onde:** projetos GCP `dev` e `prod` da organização da Alupar, região
  `us-east1` (ADRs 011 e 015).
- **Transferência internacional:** sim, para os Estados Unidos, sob o DPA do
  contrato de nuvem ([dpa.md](dpa.md)).
- **Segurança:** credenciais só no Secret Manager; criptografia em repouso com
  chave gerenciada pelo Google (ADR 015); contas de serviço com privilégio
  mínimo, verificado em teste; Portal atrás do IAP, restrito ao domínio da
  Alup; bucket raw sem acesso público. Medidas propostas no RIPD, item k.
- **Fonte:** sempre indireta — sistemas e serviços da própria controladora.
  Nenhuma coleta direta do titular.

**Fora deste registro:** as fontes públicas de mercado (BCB, IBGE, ONS, ANEEL,
CCEE, BBCE, TempoOK) não trazem dado pessoal. A ANEEL SIGA lê só dados do
empreendimento.

---

## OP-01 · Análise do desempenho comercial

| Campo | Registro |
|---|---|
| Finalidade | Acompanhar o funil comercial: negócios por *pipeline*, estágio, valor e data |
| Hipótese legal | Execução de contrato ou procedimentos preliminares (art. 7º, V) para a pessoa física que seja parte do negócio; nos demais casos, legítimo interesse (art. 7º, IX). Análise no RIPD, item g |
| Titulares | Pessoas físicas eventualmente citadas no nome do negócio |
| Dados pessoais | `nome` do negócio, texto livre. O dono do negócio (`proprietario_id`) foi retirado do conector em 11/09 |
| Dados sensíveis | Nenhum |
| Fonte | Hubspot, objeto `deals`. Contatos não são lidos |
| Sistemas | Conector `hubspot_negocios` → raw → `bronze.hubspot_negocios` → `silver.hubspot_negocios` → `gold.funil_comercial`, que agrega sem nome nem dono |
| Compartilhamento | Nenhum além dos agentes acima |
| Retenção | Raw: 90 dias. Bronze: 5 anos. Proposta na política de retenção |
| Periodicidade | A cada 6 horas, janela de 2 dias |
| Observação | Decisão de 11/09: `proprietario_id` retirado do conector, porque nenhuma tabela Gold o usava (RIPD, item g) |

## OP-02 · Controle de acesso e segurança da plataforma

| Campo | Registro |
|---|---|
| Finalidade | Autenticar quem acessa o Portal e rastrear quem consulta os dados |
| Hipótese legal | Legítimo interesse (art. 7º, IX): segurança da informação e prevenção (art. 6º, VII e VIII) |
| Titulares | Colaboradores da Alup usuários do Portal e do BigQuery; equipe da ness. durante o desenvolvimento |
| Dados pessoais | E-mail corporativo; registros de acesso e de consulta (quem, quando, o quê) |
| Dados sensíveis | Nenhum |
| Fonte | Identidade Google da Alup, via IAP; logs de *jobs* do BigQuery; Cloud Logging |
| Sistemas | Portal (Cloud Run + IAP); BigQuery; Cloud Logging |
| Compartilhamento | Nenhum além dos agentes acima |
| Retenção | Cloud Logging: 30 dias. Log de auditoria de acesso a dados, quando habilitado: 1 ano |

## OP-03 · Catalogação, linhagem e perfil dos dados

| Campo | Registro |
|---|---|
| Finalidade | Governança: catálogo, linhagem entre camadas, perfil das tabelas e glossário (ADR 014) |
| Hipótese legal | Legítimo interesse (art. 7º, IX): governança e qualidade do dado (art. 6º, V) |
| Titulares | Os mesmos de OP-01 e OP-02, de forma indireta |
| Dados pessoais | Metadados; logs de consulta com o e-mail de quem consultou; *profiling*, que lê amostra das tabelas |
| Dados sensíveis | Nenhum |
| Fonte | BigQuery, Dataform e o executor dos conectores |
| Sistemas | Knowledge Catalog, com recursos de IA generativa ativados, operados pela Alup (ADR 014) |
| Compartilhamento | Google Cloud, como suboperador |
| Retenção | Enquanto o ativo catalogado existir |
| Observação | O assistente do Dataform não é apontado para tabela com dado pessoal (ADR 012; RIPD, R05) |

## OP-04 · Portal Alup — Onda 3

| Campo | Registro |
|---|---|
| Situação | **A definir.** Aurora, DynamoDB e S3 ainda sem schema (pergunta C6) |
| Regra | Antes do conector: inventário de colunas com o dono do dado, hipótese legal e prazo; atualizar este registro e o RIPD (R06) |

## OP-05 · Sistemas internos — Onda 3

| Campo | Registro |
|---|---|
| Situação | **A definir.** Oracle FMB, MySQL de Comercialização, RM/TOTVS e SQL Server do Balanço Energético, ainda sem schema |
| Regra | Igual a OP-04. Módulos de RH e folha do RM/TOTVS ficam fora do escopo de leitura |

## OP-06 · Planilhas — Onda 4

| Campo | Registro |
|---|---|
| Situação | **A definir.** Os modelos dependem do questionário (A4) |
| Regra | Igual a OP-04 |

---

## Aprovação

| Papel | Nome | Data |
|---|---|---|
| Elaboração | ness. | 11/09/2026 |
| Encarregada | Rosimeire Miler dos Santos | |
| Controladora | ACE Comercializadora Ltda. (Alup) | |

## Histórico

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 11/09/2026 | Minuta técnica inicial, pela ness. |
| 0.2 | 11/09/2026 | Dados cadastrais da controladora e canal da encarregada; `proprietario_id` fora da OP-01 |
