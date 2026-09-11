# RIPD — Relatório de Impacto à Proteção de Dados Pessoais da plataforma AlupData

**Versão** 0.3 · **Data** 2026-09-11 · **Situação**: minuta técnica, para
revisão e aprovação da controladora

Minuta elaborada pela ness. no âmbito do contrato CPS-01025/2026, conforme a
[ADR 011](../arquitetura/decisoes/011-regiao-us-east1.md). O RIPD é documento
da controladora: a ness. descreve a plataforma e propõe a análise; a Alup
revisa, completa e assina.

Estrutura: art. 38 da LGPD e o roteiro da ANPD (itens a a l). O relatório não é
enviado à ANPD; fica mantido e é apresentado se ela o requisitar.

Documentos relacionados, em `docs/lgpd/`:

- [RoPA](ropa.md) — registro das operações (art. 37);
- [política de retenção](politica-de-retencao.md) — prazos propostos;
- [registro do DPA](dpa.md) — transferência internacional.

> **Como ler.** **[ALUP]** marca o que só a controladora pode informar ou
> decidir. Todo o resto descreve a plataforma como está no repositório em
> 11/09/2026. O que ainda não existe — schemas da Onda 3 — está dito como
> lacuna, não como fato.

---

## a) Agentes de tratamento e encarregado

| Papel | Quem | Observação |
|---|---|---|
| Controladora | ACE Comercializadora Ltda., nome fantasia Alup — CNPJ 14.402.579/0001-23; Rua Gomes de Carvalho, 1996, 16º andar, conj. 162, sala B, Vila Olímpia, São Paulo/SP, CEP 04547-905 | Definida em 11/09; dados cadastrais conferidos na Receita Federal em 11/09. As contratantes do CPS-01025/2026 são seis coligadas do Grupo Alupar; a controladora da plataforma é a ACE |
| Operadora (desenvolvimento) | ness. Processos e Tecnologia Ltda., CNPJ 72.027.097/0001-37 | Desenvolve a plataforma. O acesso a dado pessoal real fica restrito ao período de desenvolvimento e homologação (ADR 011) |
| Suboperador (infraestrutura) | Google Cloud | Processa o dado em `us-east1`, sob o DPA do contrato de nuvem da Alupar ([dpa.md](dpa.md)). A entidade contratante é a indicada nesse contrato |
| Encarregada | Rosimeire Miler dos Santos | Canal público: privacidade@alupar.com.br (art. 41, § 1º) |

As fontes de onde o dado é lido — Hubspot, o Portal Alup hospedado na AWS e os
sistemas internos — são tratamentos já existentes da controladora e ficam fora
deste relatório. Ele cobre o que acontece a partir da leitura.

## b) Outras partes interessadas

- **Donos de dado por domínio** — a matriz RACI está pendente (A5). O dono do
  dado do Hubspot é o comercial da Alup, ainda sem nome.
- **Google** — participou da revisão arquitetural de 10/09 (G1); não foi
  consultado sobre este relatório.
- **Encarregada** — Rosimeire Miler dos Santos. **[ALUP]** parecer.

## c) Justificativa

A plataforma trata sobretudo dado de mercado e de operação, sem dado pessoal
relevante. Mesmo assim o RIPD se justifica:

1. **Legítimo interesse.** É a hipótese proposta para boa parte das operações
   (item g), e o art. 10, § 3º, prevê o relatório nesse caso.
2. **Transferência internacional.** Todo o ambiente fica em `us-east1`, nos
   Estados Unidos (ADR 011, art. 33).
3. **Tecnologia com IA generativa.** O Knowledge Catalog tem recursos com o
   modelo Gemini ativados (ADR 014), e o assistente do Dataform pode rascunhar
   descrições (ADR 012) — ele lê amostra real das tabelas.
4. **Dado ainda desconhecido.** As fontes da Onda 3 não têm schema; o
   relatório fixa os critérios antes de o dado chegar.

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
6. **Eliminação.** Pelos prazos da [política de retenção](politica-de-retencao.md),
   pelo atendimento ao titular (art. 18, VI) e pela cláusula 8.3 no fim do
   contrato.

### ii. Dados pessoais tratados

| Origem | Dado pessoal | Situação |
|---|---|---|
| Hubspot — negócios (A9) | `proprietario_id` — identificador do usuário do Hubspot dono do negócio | **Retirado do conector** por decisão de 11/09 (item g); deixa de ser tratado |
| Hubspot — negócios (A9) | `nome` do negócio — texto livre, que pode conter nome de pessoa física | Confirmado no código |
| Usuários da plataforma | E-mail corporativo de quem acessa o Portal, recebido do IAP e exibido na tela | Confirmado no código (`src/portal/app.py`) |
| Usuários da plataforma | E-mail de quem executa consultas, nos logs de *jobs* do BigQuery; lido pelo Knowledge Catalog (ADR 014). A view `gold.custo_consultas` não o seleciona | Característica do serviço |
| Portal Alup (Onda 3) | **Desconhecido** — possivelmente dado de clientes | **[ALUP]** perguntas C6 e F1 |
| FMB, MySQL Comercialização, RM/TOTVS, SQL Server do Balanço (Onda 3) | **Desconhecido** | **[ALUP]** F1 |
| Planilhas (Onda 4) | **Desconhecido** — os modelos dependem do questionário (A4) | **[ALUP]** F1 |
| Fontes públicas (BCB, IBGE, ONS, ANEEL, CCEE, BBCE, TempoOK) | Nenhum. A ANEEL SIGA lê só dados do empreendimento | Confirmado nos dicionários de dados |

**Contatos do Hubspot não são lidos.** O conector lê só o objeto `deals`, com
sete propriedades — sem contatos e, desde a decisão de 11/09, sem o dono do
negócio.

### iii. Dados sensíveis

Nenhum identificado. Ponto de atenção: o RM/TOTVS é um ERP e pode ter módulos
de recursos humanos e folha, que costumam conter dado sensível. Ver R06.

### iv. Categorias de titulares

- Colaboradores da Alup usuários do Portal e do BigQuery.
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

Três finalidades, detalhadas no [RoPA](ropa.md):

- **F1** — análise do desempenho comercial (OP-01);
- **F2** — controle de acesso e segurança da plataforma (OP-02);
- **F3** — governança: catálogo, linhagem e perfil dos dados (OP-03).

As fontes da Onda 3 e as planilhas ganham finalidade própria quando o schema
for conhecido (OP-04 a OP-06).

### ix. Compartilhamento

- Google Cloud, como suboperador de infraestrutura.
- ness., como operadora, durante o desenvolvimento e a homologação.
- Nenhum outro destinatário. A ferramenta de BI ainda não foi definida (A6);
  quando for, este relatório é revisto.

### x. Armazenamento, retenção e transferência internacional

**Hoje** nada é excluído: o bucket raw só muda de classe aos 90 dias, o
versionamento guarda cópias antigas e o BigQuery não tem expiração. A
[política de retenção](politica-de-retencao.md) propõe os prazos por camada e
por conteúdo — por exemplo, raw com dado pessoal excluído aos 90 dias e Bronze
com dado pessoal expirando em 5 anos. Os prazos passam a valer quando
aprovados e declarados em `infra/`.

**Transferência internacional (art. 33).** Todo o dado fica em `us-east1`. A
transferência se apoia no DPA do contrato de nuvem da Alupar; o
[registro do DPA](dpa.md) detalha o mecanismo.

## g) Hipótese legal

Análise proposta pela ness. **[ALUP]** Validação do jurídico e da encarregada.

| Finalidade | Dado | Titular | Hipótese proposta |
|---|---|---|---|
| F1 | `proprietario_id` | Colaborador dono do negócio | Não se aplica: retirado do conector em 11/09 |
| F1 | `nome` do negócio | Pessoa física citada | Execução de contrato ou procedimentos preliminares (art. 7º, V), quando ela é parte do negócio; nos demais casos, legítimo interesse |
| F2 | E-mail e registros de acesso e consulta | Usuário da plataforma | Legítimo interesse (art. 7º, IX) |
| F3 | Metadados e logs de consulta | Usuário da plataforma, indiretamente | Legítimo interesse (art. 7º, IX) |

**Consentimento não é recomendado** para colaboradores: a assimetria da relação
de trabalho compromete o caráter livre do consentimento.

### Teste de balanceamento do legítimo interesse

Modelo do Guia Orientativo da ANPD sobre legítimo interesse (fevereiro de
2024), em três fases.

**F1 — dono do negócio (`proprietario_id`)**

1. **Finalidade.** Gerir o desempenho comercial da própria empresa é interesse
   legítimo, concreto e lícito.
2. **Necessidade.** **Não atendida hoje.** O dado é mínimo — um identificador,
   sem nome nem e-mail —, mas **nenhuma tabela Gold o usa**: `funil_comercial`
   agrega por *pipeline* e estágio, sem dono. O dado entra na Bronze e na
   Silver sem finalidade que o exija.
3. **Balanceamento.** O titular espera que o CRM corporativo seja usado para
   gestão comercial; o impacto é baixo.

**Decisão de 11/09:** recomendação acatada. `proprietario_id` sai do conector,
e o dado deixa de ser tratado. Se a Alup quiser, no futuro, funil por
responsável, o dado volta com essa finalidade e com este teste refeito.

**F2 — controle de acesso e segurança**

1. **Finalidade.** Proteger a plataforma e o dado nela é interesse legítimo e
   atende aos princípios de segurança e prevenção (art. 6º, VII e VIII).
2. **Necessidade.** Atendida: sem identificar o usuário não há autenticação
   nem rastreabilidade.
3. **Balanceamento.** O titular é colaborador usando sistema corporativo; a
   expectativa de controle de acesso é razoável. Salvaguardas: acesso restrito
   ao domínio da Alup, retenção limitada (30 dias de log, 1 ano de auditoria) e
   uso restrito à segurança.

**F3 — governança**

1. **Finalidade.** Catálogo, linhagem e qualidade atendem ao princípio da
   qualidade dos dados (art. 6º, V).
2. **Necessidade.** Atendida para metadados. O e-mail nos logs de consulta é
   efeito colateral do serviço, não objetivo.
3. **Balanceamento.** Impacto baixo. Salvaguarda: conteúdo gerado por IA fica
   marcado `origem = automatica` e não homologa (ADR 014).

**Transparência (art. 10, § 2º).** **[ALUP]** Informar os colaboradores, em
aviso interno de privacidade, sobre o uso de dados de F2 e F3.

## h) Princípios da LGPD (art. 6º)

| Princípio | Como a plataforma atende | Lacuna |
|---|---|---|
| Finalidade e adequação | Finalidades F1 a F3 declaradas no RoPA | Onda 3 a definir |
| Necessidade | O Hubspot lê só 7 propriedades de negócios, sem contatos nem dono do negócio; a Gold não expõe o nome; prazos propostos na política de retenção | — |
| Livre acesso | Canal da encarregada, privacidade@alupar.com.br; eliminação a pedido na política de retenção | — |
| Qualidade | Validação na carga, deduplicação na Silver, *assertions* do Dataform | — |
| Transparência | Dicionário de dados, linhagem por fonte, este relatório e o RoPA | Aviso interno aos colaboradores (item g) |
| Segurança e prevenção | Ver item k | R01, R07 |
| Não discriminação | Não há decisão automatizada sobre titulares | — |
| Responsabilização | Decisões em ADRs versionadas; histórico de commits | — |

## i) Riscos ao titular

| # | Risco |
|---|---|
| R01 | Acesso indevido a dado pessoal: nenhum acesso de pessoas está declarado no Terraform, e o IAP do Portal está fora dele |
| R02 | Retenção indefinida: o bucket raw e o BigQuery não excluem nada, e a eliminação da cláusula 8.3 não tem procedimento |
| R03 | Transferência internacional sem mecanismo adequado |
| R04 | Dado pessoal em texto livre (nome do negócio) propagado da Bronze para a Silver e para o catálogo |
| R05 | Dado pessoal exposto a recursos de IA: o assistente do Dataform lê amostra real, e o Knowledge Catalog processa logs de consulta com e-mails |
| R06 | Dado pessoal ou sensível não previsto chegando pelas fontes da Onda 3, que ainda não têm schema |
| R07 | Rastreabilidade insuficiente: não há log de auditoria de acesso a dados configurado |
| R08 | Acesso da ness. a dado real além do período de desenvolvimento e homologação |
| R09 | Vazamento de credencial de fonte, dando acesso ao dado na origem |
| R10 | Dado real de titular gravado no repositório de código |

## j) Avaliação

Metodologia: probabilidade (P) e impacto (I) de 1 a 3; nível = P × I. **Baixo**
de 1 a 2, **médio** de 3 a 4, **alto** de 6 a 9. Avaliação proposta pela ness.;
**[ALUP]** valida.

| # | P | I | Nível antes das medidas | Nível residual esperado |
|---|---|---|---|---|
| R01 | 2 | 3 | **Alto (6)** | Baixo |
| R02 | 3 | 2 | **Alto (6)** | Baixo, com a política de retenção em `infra/` |
| R03 | 1 | 2 | Baixo (2) — há DPA | Baixo |
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
| R01 | Acesso de pessoas por grupo, declarado em `infra/`: consumidores leem a Gold; Bronze e Silver só para quem opera — PR #118 | P |
| R01 | IAP e serviço do Portal no Terraform, com conta de serviço própria — PR #118 | P |
| R01 | Controle de acesso por coluna (*policy tags* do BigQuery) nas colunas com dado pessoal | P |
| R02 | Prazos da [política de retenção](politica-de-retencao.md) declarados em `infra/`: exclusão no bucket raw, exclusão de versões antigas, expiração de partição na Bronze | P |
| R02 | Procedimento de eliminação a pedido do titular e da cláusula 8.3, no runbook | P |
| R03 | DPA do contrato de nuvem da Alupar ([dpa.md](dpa.md)) | E |
| R04 | A Gold não expõe `nome` nem `proprietario_id`: `funil_comercial` só agrega | E |
| R04 | Colunas com dado pessoal marcadas no catálogo e cobertas pela *policy tag* de R01 | P |
| R04 | `proprietario_id` retirado do conector, por decisão de 11/09 (item g) — PR #116 | P |
| R05 | O assistente do Dataform só entra por PR e não é apontado para tabela com dado pessoal (ADR 012); conteúdo gerado no catálogo fica `origem = automatica` e não homologa (ADR 014) | E |
| R05 | Manter o assistente fora das tabelas com colunas marcadas como pessoais **também depois** da aprovação deste relatório | P |
| R06 | Antes de cada conector da Onda 3: inventário de colunas com o dono do dado; seleção explícita de colunas, nunca `SELECT *`; módulos de RH e folha fora do escopo de leitura; hipótese legal e prazo definidos; revisão deste relatório e do RoPA | P |
| R07 | Log de auditoria de acesso a dados (*Data Access audit logs*) do BigQuery e do Cloud Storage, declarado em `infra/` — PR #118. Retenção padrão de 30 dias; 1 ano depende da política de retenção. O custo é da Alup | P |
| R08 | Acesso da ness. por grupo, com revogação na homologação final e no handoff (cláusula 8.3) | P |
| R09 | Credenciais só no Secret Manager; deploy via WIF, sem chave; gitleaks no CI e no pre-commit; teste que impede a senha de aparecer em mensagem de erro | E |
| R10 | Regra de não ter dado real no repositório (`AGENTS.md`, `SECURITY.md`); fixtures sintéticos | E |

## l) Comentários e aprovações

| Papel | Nome | Data | Parecer |
|---|---|---|---|
| Elaboração da minuta técnica | ness. | 11/09/2026 | Versão 0.3 |
| Encarregada | Rosimeire Miler dos Santos | | |
| Controladora | ACE Comercializadora Ltda. (Alup) | | |

---

## Pendências para fechar a versão 1.0

1. Validação das hipóteses legais e do teste de balanceamento (item g).
2. Aprovação da política de retenção (item f.x, R02).
3. Dado pessoal do Portal Alup e das demais fontes da Onda 3 — perguntas C6 e F1
   (itens f.ii, R06).
4. Aviso interno de privacidade aos colaboradores (item g).
5. Validação da avaliação de risco (item j).
6. Entidade Google contratante e destinatário das notificações de
   subprocessador ([registro do DPA](dpa.md)).

## Histórico

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 11/09/2026 | Minuta técnica inicial, pela ness. |
| 0.2 | 11/09/2026 | Controladora e encarregada definidas; análise de hipótese legal com teste de balanceamento; política de retenção e DPA referenciados; R03 reavaliado |
| 0.3 | 11/09/2026 | Dados cadastrais da controladora (Receita Federal) e canal da encarregada; `proprietario_id` retirado do conector por decisão da Alup |
