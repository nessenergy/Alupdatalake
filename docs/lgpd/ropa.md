# RoPA — Registro das Operações de Tratamento da plataforma AlupData

**Versão** 0.3 · **Data** 2026-09-11 · **Situação**: minuta técnica, para
revisão e aprovação da controladora

Registro exigido pelo art. 37 da LGPD. Minuta elaborada pela ness. no contrato
CPS-01025/2026 ([ADR 011](../arquitetura/decisoes/011-regiao-us-east1.md)). A
análise de risco está no [RIPD](ripd.md), os prazos na
[política de retenção](politica-de-retencao.md) e a transferência internacional
no [registro do DPA](dpa.md). As perguntas citadas (F1, E4 e outras) são as do
[Questionário de Gaps](../questionario-gaps.md), respondidas pela Alup em 11/09.

## Agentes

| Papel | Quem |
|---|---|
| Controladora | ACE Comercializadora Ltda., nome fantasia Alup — CNPJ 14.402.579/0001-23 |
| Encarregada | Rosimeire Miler dos Santos — privacidade@alupar.com.br |
| Operadora (desenvolvimento) | ness. Processos e Tecnologia Ltda., CNPJ 72.027.097/0001-37 — até o handoff |
| Suboperador (infraestrutura) | Google Cloud, sob o DPA do contrato de nuvem da Alupar |

## Comum a todas as operações

- **Onde:** projetos GCP `dev`, `hml` e `prod` da organização da Alupar, região
  `us-east1` (ADR 011; pergunta E4). O dado oficial fica em `prod`; `dev` e
  `hml` guardam cópia por 30 e 90 dias. O `infra/` declara hoje `dev` e `prod`,
  e a ADR 015, que previa dois ambientes, será revista.
- **Transferência internacional:** sim, para os Estados Unidos, sob o DPA do
  contrato de nuvem ([dpa.md](dpa.md)).
- **Classificação:** datasets e bucket raw classificados como **internos**
  (pergunta F4).
- **Segurança:** credenciais só no Secret Manager; criptografia em repouso com
  chave gerenciada pelo Google (ADR 015); contas de serviço com privilégio
  mínimo, verificado em teste; Portal atrás do IAP, restrito ao domínio da
  Alup; bucket raw sem acesso público. Sem mascaramento nem pseudonimização
  (pergunta F2): o **controle de acesso por tipo de usuário**, por coluna e por
  linha, é requisito, ainda a implementar (RIPD, item k, R01).
- **Retenção:** pela [política de retenção](politica-de-retencao.md) 0.2 —
  mínimo de 5 anos, contados a partir de 2027; exceções em cada operação.
- **Fonte:** sempre indireta — sistemas e serviços da própria controladora e a
  CCEE, da qual ela é agente. Nenhuma coleta direta do titular.

**Fora deste registro:** as fontes públicas de mercado (BCB, IBGE, ONS, ANEEL,
CCEE pública) e as licenciadas (BBCE, TempoOK) não trazem dado pessoal. A ANEEL
SIGA lê só dados do empreendimento.

---

## OP-01 · Análise do desempenho comercial

| Campo | Registro |
|---|---|
| Finalidade | Acompanhar o funil comercial: negócios por *pipeline*, estágio, valor e data |
| Hipótese legal | Execução de contrato ou procedimentos preliminares (art. 7º, V) para a pessoa física que seja parte do negócio; nos demais casos, legítimo interesse (art. 7º, IX). Análise no RIPD, item g |
| Titulares | Pessoas físicas citadas no nome do negócio ou partes dele |
| Dados pessoais | `nome` do negócio, texto livre; `valor` do negócio, quando o negócio identifica pessoa física. O dono do negócio (`proprietario_id`) foi retirado do conector em 11/09 |
| Dados confidenciais (pergunta F1) | Valor de contrato, lido hoje. CNPJ, CPF e endereço estão no Hubspot da Alup, mas nos objetos de empresa e de contato, que o conector não lê |
| Dados sensíveis (art. 5º, II) | Nenhum. O que a pergunta F1 chama de sensível é confidencial; ver RIPD, item f.iii |
| Fonte | Hubspot, objeto `deals`. Contatos e empresas não são lidos |
| Sistemas | Conector `hubspot_negocios` → raw → `bronze.hubspot_negocios` → `silver.hubspot_negocios` → `gold.funil_comercial`, que agrega sem nome nem dono |
| Compartilhamento | Nenhum além dos agentes acima |
| Retenção | Raw: 5 anos, contados de 2027, em classe fria (recomendação; a alternativa de 90 dias está em decisão). Bronze: 5 anos, contados de 2027. Gold: recalculada a partir da Bronze |
| Periodicidade | A cada 6 horas, janela de 2 dias |
| Observação | Decisão de 11/09: `proprietario_id` retirado do conector, porque nenhuma tabela Gold o usava (RIPD, item g). **O escopo de contatos e empresas do Hubspot está em confirmação com a Alup.** Se entrar, o CPF passa a ser tratado, e este registro e o RIPD são revistos antes do conector |

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
| Retenção | Cloud Logging: 30 dias. Log de auditoria de acesso a dados: 1 ano, nos três projetos |

## OP-03 · Catalogação, linhagem e perfil dos dados

| Campo | Registro |
|---|---|
| Finalidade | Governança: catálogo, linhagem entre camadas, perfil das tabelas e glossário (ADR 014) |
| Hipótese legal | Legítimo interesse (art. 7º, IX): governança e qualidade do dado (art. 6º, V) |
| Titulares | Os mesmos de OP-01, OP-02 e OP-07, de forma indireta |
| Dados pessoais | Metadados; logs de consulta com o e-mail de quem consultou; *profiling*, que lê amostra das tabelas |
| Dados sensíveis | Nenhum |
| Fonte | BigQuery, Dataform e o executor dos conectores |
| Sistemas | Knowledge Catalog, com recursos de IA generativa ativados, operados pela Alup (ADR 014) |
| Compartilhamento | Google Cloud, como suboperador |
| Retenção | Enquanto o ativo catalogado existir |
| Observação | O assistente do Dataform não é apontado para tabela com dado pessoal ou confidencial (ADR 012; RIPD, R05) |

## OP-04 · Portal Alup — Onda 3

| Campo | Registro |
|---|---|
| Situação | **A definir.** Aurora, DynamoDB e S3 ainda sem schema (pergunta C6) |
| Regra | Antes do conector: inventário de colunas com o dono do dado, hipótese legal, prazo e *policy tag*; atualizar este registro e o RIPD (R06) |

## OP-05 · Sistemas internos — Onda 3

| Campo | Registro |
|---|---|
| Situação | **A definir.** Oracle FMB, MySQL de Comercialização, RM/TOTVS e SQL Server do Balanço Energético, ainda sem schema. Pela pergunta F1, os dados da Comercialização e o balanço energético são confidenciais; nenhum dado pessoal foi apontado |
| Regra | Igual a OP-04. Módulos de RH e folha do RM/TOTVS ficam fora do escopo de leitura |
| Retenção | Regra geral: 5 anos na Bronze, contados de 2027 |

## OP-06 · Planilhas — Onda 4

| Campo | Registro |
|---|---|
| Situação | **A definir.** Os modelos dependem do questionário (A4). Pela pergunta F1, as planilhas geradas internamente — premissas de GSF, preço e outras variáveis calculadas pela Comercialização — são confidenciais; nenhum dado pessoal foi apontado |
| Regra | Igual a OP-04 |
| Retenção | Regra geral: 5 anos na Bronze, contados de 2027 |

## OP-07 · Consumo realizado por cliente — CCEE

| Campo | Registro |
|---|---|
| Situação | **A definir.** Ainda sem conector. A fonte exata — CCEE com credencial de agente (plano, item 2.1) ou InfoMercado (item 1.1) — está a definir |
| Finalidade | Gestão da carteira de clientes: consumo realizado por cliente (RIPD, finalidade F4) |
| Hipótese legal | Execução de contrato (art. 7º, V), para o cliente pessoa física. **[ALUP]** confirmar |
| Titulares | Clientes pessoa física da comercializadora. O consumo de cliente pessoa jurídica é confidencial, mas não é dado pessoal; o de cliente pessoa física é dado pessoal |
| Dados pessoais | Consumo realizado e identificação do cliente, quando pessoa física |
| Dados confidenciais (pergunta F1) | Consumo realizado por cliente, de qualquer cliente |
| Dados sensíveis (art. 5º, II) | Nenhum |
| Fonte | CCEE |
| Sistemas | Conector a escrever → raw → Bronze → Silver → Gold mensal por cliente, incremental e protegida contra recálculo total |
| Compartilhamento | Nenhum além dos agentes acima |
| Retenção | **Exceção da pergunta F3:** Bronze, 5 anos; Gold mensal, 10 anos — ambos contados de 2027. Raw: 5 anos, em classe fria (recomendação) |
| Regra | Igual a OP-04: coluna de consumo e identificação do cliente com *policy tag*, leitura só para os tipos de usuário autorizados (pergunta F2) |

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
| 0.3 | 11/09/2026 | Respostas da Alup de 11/09: dados confidenciais na OP-01, com o escopo de contatos e empresas do Hubspot em confirmação; nova OP-07 para o consumo por cliente; planilhas e dados internos confidenciais nas OP-05 e OP-06; retenções pela política 0.2; classificação interna; controle de acesso por tipo de usuário como requisito; três ambientes |
