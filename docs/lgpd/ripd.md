# RIPD — Relatório de Impacto à Proteção de Dados Pessoais da plataforma AlupData

**Versão** 0.1 · **Data** 2026-09-11 · **Situação**: minuta técnica, para revisão,
complementação e aprovação da controladora

Minuta elaborada pela ness. no âmbito do contrato CPS-01025/2026, conforme a
[ADR 011](../arquitetura/decisoes/011-regiao-us-east1.md). O RIPD é documento
da controladora: a ness. descreve a plataforma e propõe a análise de risco; a
controladora revisa, completa e assina.

Estrutura: art. 38 da LGPD e o roteiro da ANPD (itens a a l). O relatório não é
enviado à ANPD; fica mantido e é apresentado se ela o requisitar.

> **Como ler.** **[ALUP]** marca o que só a controladora pode informar ou
> decidir. Todo o resto descreve a plataforma como está no repositório em
> 11/09/2026. O que ainda não existe — schemas da Onda 3, políticas de
> retenção — está dito como lacuna, não como fato.

---

## a) Agentes de tratamento e encarregado

| Papel | Quem | Observação |
|---|---|---|
| Controladora | **[ALUP]** | As contratantes do CPS-01025/2026 são seis coligadas do Grupo Alupar (FGE, IJUI, FOZ, QUELUZ, LAVRINHAS e VERDE 08); a organização GCP é da Alupar. Definir se a controladora é cada coligada, uma delas ou se há controladoria conjunta. |
| Operadora (desenvolvimento) | ness. Processos e Tecnologia Ltda., CNPJ 72.027.097/0001-37 | Desenvolve a plataforma. O acesso a dado pessoal real fica restrito ao período de desenvolvimento e homologação (ADR 011). |
| Suboperador (infraestrutura) | Google Cloud | Processa o dado na região `us-east1`, sob o contrato de nuvem da Alupar e o *Cloud Data Processing Addendum*. **[ALUP]** confirmar a entidade contratante. |
| Encarregado | **[ALUP]** | Nome e contato. |

As fontes de onde o dado é lido — Hubspot, o Portal Alup hospedado na AWS e os
sistemas internos — são tratamentos já existentes da controladora e ficam fora
deste relatório. Ele cobre o que acontece a partir da leitura.

## b) Outras partes interessadas

- **Donos de dado por domínio** — a matriz RACI está pendente (A5). O dono do
  dado do Hubspot é o comercial da Alup, ainda sem nome.
- **Google** — participou da revisão arquitetural de 10/09 (G1); não foi
  consultado sobre este relatório.
- **[ALUP]** Compliance e encarregado: pareceres.

## c) Justificativa

A plataforma trata sobretudo dado de mercado e de operação, sem dado pessoal
relevante. Mesmo assim o RIPD se justifica por prevenção e gestão de risco:

1. **Transferência internacional.** Todo o ambiente fica em `us-east1`, nos
   Estados Unidos (ADR 011, art. 33).
2. **Tecnologia com IA generativa.** O Knowledge Catalog tem recursos com o
   modelo Gemini ativados (ADR 014), e o assistente do Dataform pode ser usado
   para rascunhar descrições (ADR 012) — ele lê amostra real das tabelas.
3. **Dado ainda desconhecido.** As fontes da Onda 3 não têm schema; o
   relatório registra os critérios antes de o dado chegar.

## d) Projeto que justifica o relatório

Plataforma AlupData: data lake em arquitetura *medallion* (Bronze, Silver, Gold)
no Google Cloud, que consolida 13 fontes de dado de mercado de energia, operação
e comercial em quatro ondas, para análise e indicadores da Alup. Contrato
CPS-01025/2026, de 27/08/2026 a 08/01/2027.

## e) Sistemas envolvidos

| Sistema | Papel | Onde |
|---|---|---|
| Cloud Storage, bucket `<projeto>-raw` | Guarda o registro bruto de cada leitura, antes de qualquer tratamento | `infra/modules/storage` |
| BigQuery: `bronze`, `silver`, `gold` | Camadas do lake; `qualidade` guarda linhas que falharam regra de qualidade | `infra/modules/bigquery` |
| Cloud Run Jobs | Executor dos conectores | `infra/` |
| Cloud Scheduler | Agenda as leituras | `infra/modules/scheduler` |
| Secret Manager | Credenciais das fontes | `infra/modules/secrets` |
| Dataform | Transformação Bronze → Silver → Gold | ADR 012 |
| Knowledge Catalog | Catálogo, linhagem e *profiling* | ADR 014 — ainda fora do Terraform |
| Cloud Logging | Logs de execução, 30 dias | padrão do serviço |
| Portal (Cloud Run + IAP) | Consulta das tabelas Gold, saúde e custo | ADR 005 — IAP ainda fora do Terraform |

A região-alvo é `us-east1` (ADR 011). No `infra/` da `main` ainda consta
`southamerica-east1`; a troca está no PR de infraestrutura e acontece antes do
primeiro `apply`.

## f) Tratamento de dados

### i. Descrição do tratamento

1. **Coleta.** O conector lê a fonte por janela de datas. Não há coleta direta
   do titular.
2. **Armazenamento bruto.** O registro lido é gravado no bucket raw, em
   `<fonte>/<entidade>/dt=AAAA-MM-DD/`, antes de qualquer validação.
3. **Carga.** Linhas válidas vão para a Bronze, que só recebe acréscimos;
   linhas inválidas são descartadas e contadas.
4. **Transformação.** A Silver deduplica e padroniza; a Gold calcula
   indicadores.
5. **Consulta.** Portal e, no futuro, ferramenta de BI (A6).
6. **Eliminação.** Prevista na cláusula 8.3 do contrato para dado de teste e de
   produção após a homologação; o procedimento ainda não existe (ver R02).

### ii. Dados pessoais tratados

| Origem | Dado pessoal | Situação |
|---|---|---|
| Hubspot — negócios (A9) | `proprietario_id` — identificador do usuário do Hubspot dono do negócio, colaborador da Alup | Confirmado no código (`src/conectores/hubspot_negocios.py`) |
| Hubspot — negócios (A9) | `nome` do negócio — texto livre, que pode conter nome de pessoa física | Confirmado no código |
| Usuários da plataforma | E-mail corporativo de quem acessa o Portal, recebido do IAP e exibido na tela | Confirmado no código (`src/portal/app.py`) |
| Usuários da plataforma | E-mail de quem executa consultas, nos logs de *jobs* do BigQuery; lido pelo Knowledge Catalog (ADR 014). A view `gold.custo_consultas` não o seleciona | Característica do serviço |
| Portal Alup (Onda 3) | **Desconhecido** — possivelmente dado de clientes | **[ALUP]** perguntas C6 e F1 |
| FMB, MySQL Comercialização, RM/TOTVS, SQL Server do Balanço (Onda 3) | **Desconhecido** | **[ALUP]** F1 |
| Planilhas (Onda 4) | **Desconhecido** — os modelos dependem do questionário (A4) | **[ALUP]** F1 |
| Fontes públicas (BCB, IBGE, ONS, ANEEL, CCEE, BBCE, TempoOK) | Nenhum. A ANEEL SIGA lê só dados do empreendimento | Confirmado nos dicionários de dados |

**Contatos do Hubspot não são lidos.** O conector lê só o objeto `deals`, com
oito propriedades.

### iii. Dados sensíveis

Nenhum identificado. Ponto de atenção: o RM/TOTVS é um ERP e pode ter módulos
de recursos humanos e folha, que costumam conter dado sensível. Ver R06.

### iv. Categorias de titulares

- Colaboradores da Alup: donos de negócio no Hubspot e usuários do Portal e do
  BigQuery.
- Pessoas físicas eventualmente citadas no nome livre de um negócio.
- **[ALUP]** Titulares do Portal Alup e dos sistemas internos.

### v. Titulares vulneráveis

Nenhum previsto. **[ALUP]** confirmar no Portal Alup.

### vi. Volume

- Hubspot: desconhecido; o conector ainda não rodou contra a conta real (A9).
- Portal Alup, estimativa da reunião de 10/09: 2 GB no Aurora, 3 GB no
  DynamoDB, cerca de 8 GB no S3.
- FMB: desconhecido (C6).
- **[ALUP]** Número de titulares.

### vii. Fonte

Indireta: sistemas e serviços da própria controladora.

### viii. Finalidade

Consolidar dado de mercado de energia, operação e desempenho comercial para
análise e indicadores de gestão. **[ALUP]** validar e detalhar por domínio.

### ix. Compartilhamento

- Google Cloud, como suboperador de infraestrutura.
- ness., como operadora, durante o desenvolvimento e a homologação.
- Nenhum outro destinatário. A ferramenta de BI ainda não foi definida (A6);
  quando for, este relatório é revisto.

### x. Armazenamento, retenção e transferência internacional

| Onde | Hoje | Lacuna |
|---|---|---|
| Bucket raw | Passa para a classe NEARLINE após 90 dias; **nunca é excluído**; o versionamento guarda cópias antigas | Sem prazo de exclusão |
| BigQuery | Nenhuma expiração de tabela, partição ou dataset | Sem prazo de exclusão |
| Cloud Logging | 30 dias | — |
| Eliminação ao fim do contrato | Cláusula 8.3 | Sem procedimento escrito |

A política de retenção por camada depende da pergunta F3. **[ALUP]**

**Transferência internacional (art. 33).** Todo o dado fica em `us-east1`. O
mecanismo de transferência precisa ser formalizado. **[ALUP]** Confirmar com o
jurídico se o contrato de nuvem da Alupar incorpora as cláusulas-padrão
contratuais da ANPD (Resolução CD/ANPD nº 19/2024) ou indicar outro mecanismo
do art. 33.

## g) Hipótese legal

**[ALUP]** Uma hipótese por finalidade.

Como ponto de partida para o jurídico, e não como decisão: o dado de
colaboradores (dono do negócio, usuário do Portal) costuma se enquadrar em
legítimo interesse (art. 7º, IX) ou execução de contrato (art. 7º, V). Se a
escolha for legítimo interesse, o art. 10, § 3º, já recomenda este relatório.

## h) Princípios da LGPD (art. 6º)

| Princípio | Como a plataforma atende | Lacuna |
|---|---|---|
| Finalidade e adequação | Uso analítico, declarado no contrato | **[ALUP]** finalidade por domínio |
| Necessidade | O Hubspot lê só 8 propriedades de negócios, sem contatos; a Gold `funil_comercial` agrega por *pipeline* e estágio, sem nome nem dono | Retenção indefinida (R02) |
| Livre acesso | — | **[ALUP]** canal do titular |
| Qualidade | Validação na carga, deduplicação na Silver, *assertions* do Dataform | — |
| Transparência | Dicionário de dados e linhagem por fonte | — |
| Segurança e prevenção | Ver item k | R01, R07 |
| Não discriminação | Não há decisão automatizada sobre titulares | — |
| Responsabilização | Decisões em ADRs versionadas; histórico de commits | — |

## i) Riscos ao titular

| # | Risco |
|---|---|
| R01 | Acesso indevido a dado pessoal: nenhum acesso de pessoas está declarado no Terraform, e o IAP do Portal está fora dele |
| R02 | Retenção indefinida: o bucket raw e o BigQuery não excluem nada, e a eliminação da cláusula 8.3 não tem procedimento |
| R03 | Transferência internacional sem mecanismo formalizado |
| R04 | Dado pessoal em texto livre (nome do negócio) propagado da Bronze para a Silver e para o catálogo |
| R05 | Dado pessoal exposto a recursos de IA: o assistente do Dataform lê amostra real, e o Knowledge Catalog processa logs de consulta com e-mails |
| R06 | Dado pessoal ou sensível não previsto chegando pelas fontes da Onda 3, que ainda não têm schema |
| R07 | Rastreabilidade insuficiente: não há log de auditoria de acesso a dados configurado |
| R08 | Acesso da ness. a dado real além do período de desenvolvimento e homologação |
| R09 | Vazamento de credencial de fonte, dando acesso ao dado na origem |
| R10 | Dado real de titular gravado no repositório de código |

## j) Avaliação

Metodologia: probabilidade (P) e impacto (I) de 1 a 3; nível = P × I. **Baixo**
de 1 a 2, **médio** de 3 a 4, **alto** de 6 a 9. A avaliação é a proposta
técnica da ness.; **[ALUP]** valida.

| # | P | I | Nível antes das medidas | Nível residual esperado |
|---|---|---|---|---|
| R01 | 2 | 3 | **Alto (6)** | Baixo |
| R02 | 3 | 2 | **Alto (6)** | Baixo |
| R03 | 2 | 2 | Médio (4) | Baixo |
| R04 | 2 | 1 | Baixo (2) | Baixo |
| R05 | 2 | 2 | Médio (4) | Baixo |
| R06 | 2 | 3 | **Alto (6)** | Médio, até cada schema ser conhecido |
| R07 | 2 | 2 | Médio (4) | Baixo |
| R08 | 1 | 2 | Baixo (2) | Baixo |
| R09 | 1 | 3 | Médio (3) | Baixo |
| R10 | 1 | 1 | Baixo (1) | Baixo |

## k) Medidas, salvaguardas e mecanismos de mitigação

**E** = existe hoje · **P** = proposta, a implementar em `infra/` ou no código
(regra 5).

| # | Medida | Tipo |
|---|---|---|
| R01 | Contas de serviço com privilégio mínimo, verificado em teste (`tests/unit/test_infra.py`); Portal atrás do IAP, restrito ao domínio da Alup, que recusa requisição sem identidade | E |
| R01 | Acesso de pessoas por grupo, declarado em `infra/`: consumidores leem a Gold; Bronze e Silver só para quem opera | P |
| R01 | Trazer o IAP e o serviço do Portal para o Terraform | P |
| R01 | Controle de acesso por coluna (*policy tags* do BigQuery) nas colunas com dado pessoal | P |
| R02 | Regra de exclusão no bucket raw e limite de versões antigas, no prazo definido em F3 | P |
| R02 | Expiração de partição na Bronze, conforme F3 | P |
| R02 | Procedimento de eliminação da cláusula 8.3 escrito no runbook | P |
| R03 | *Cloud Data Processing Addendum* aceito pela Alupar | E |
| R03 | Mecanismo do art. 33 formalizado e registrado no RoPA **[ALUP]** | P |
| R04 | A Gold não expõe `nome` nem `proprietario_id`: `funil_comercial` só agrega | E |
| R04 | Colunas com dado pessoal marcadas no catálogo e cobertas pela *policy tag* de R01 | P |
| R05 | O assistente do Dataform só entra por PR e não é apontado para tabela com dado pessoal (ADR 012); conteúdo gerado no catálogo fica `origem = automatica` e não homologa (ADR 014) | E |
| R05 | Manter o assistente fora das tabelas com colunas marcadas como pessoais **também depois** da aprovação deste relatório | P |
| R06 | Antes de cada conector da Onda 3: inventário de colunas com o dono do dado; seleção explícita de colunas, nunca `SELECT *`; módulos de RH e folha fora do escopo de leitura; revisão deste relatório | P |
| R07 | Log de auditoria de acesso a dados (*Data Access audit logs*) do BigQuery e do Cloud Storage, declarado em `infra/`. O custo é da Alup | P |
| R08 | Acesso da ness. por grupo, com revogação na homologação final e no handoff (cláusula 8.3) | P |
| R09 | Credenciais só no Secret Manager; deploy via WIF, sem chave; gitleaks no CI e no pre-commit; teste que impede a senha de aparecer em mensagem de erro | E |
| R10 | Regra de não ter dado real no repositório (`AGENTS.md`, `SECURITY.md`); fixtures sintéticos | E |

## l) Comentários e aprovações

| Papel | Nome | Data | Parecer |
|---|---|---|---|
| Elaboração da minuta técnica | ness. | 11/09/2026 | Versão 0.1 |
| Encarregado | **[ALUP]** | | |
| Controladora | **[ALUP]** | | |

---

## Pendências para fechar a versão 1.0

1. Definir a controladora e o encarregado (item a).
2. Hipótese legal por finalidade (item g).
3. Política de retenção por camada — pergunta F3 (itens f.x, R02).
4. Mecanismo de transferência internacional (item f.x, R03).
5. Dado pessoal do Portal Alup e das demais fontes da Onda 3 — perguntas C6 e F1
   (itens f.ii, R06).
6. Validar a avaliação de risco (item j).

## Histórico

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 11/09/2026 | Minuta técnica inicial, pela ness. |
