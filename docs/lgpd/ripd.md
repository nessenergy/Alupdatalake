# RIPD — Relatório de Impacto à Proteção de Dados Pessoais da plataforma AlupData

**Versão** 0.7 · **Data** 2026-09-14 · **Situação**: minuta técnica, para
revisão e aprovação da controladora

Minuta elaborada pela ness. no âmbito do contrato CPS-01025/2026, conforme a
[ADR 023](../arquitetura/decisoes/023-regiao-us-central1.md). O RIPD é documento
da controladora: a ness. descreve a plataforma e propõe a análise; a Alup
revisa, completa e assina.

Estrutura: art. 38 da LGPD e o roteiro da ANPD (itens a a l). O relatório não é
enviado à ANPD; fica mantido e é apresentado se ela o requisitar.

Documentos relacionados, em `docs/lgpd/`:

- [RoPA](ropa.md) — registro das operações (art. 37);
- [política de retenção](politica-de-retencao.md) — prazos, com os critérios
  da Alup de 11/09;
- [registro do DPA](dpa.md) — transferência internacional.

> **Como ler.** **[ALUP]** marca o que só a controladora pode informar ou
> decidir. Todo o resto descreve a plataforma como está no repositório em
> 11/09/2026. O que ainda não existe — schemas da Onda 3, conector de consumo
> por cliente — está dito como lacuna, não como fato.
>
> As respostas da Alup ao [Questionário de Gaps](../questionario-gaps.md), de
> 11/09, são citadas como "pergunta F1", "pergunta E4" e assim por diante. F1 a
> F4 sem a palavra "pergunta" são as finalidades deste relatório (item f.viii).

---

## a) Agentes de tratamento e encarregado

| Papel | Quem | Observação |
|---|---|---|
| Controladora | ACE Comercializadora Ltda., nome fantasia Alup — CNPJ 14.402.579/0001-23; Rua Gomes de Carvalho, 1996, 16º andar, conj. 162, sala B, Vila Olímpia, São Paulo/SP, CEP 04547-905 | Definida em 11/09; dados cadastrais conferidos na Receita Federal em 11/09. As contratantes do CPS-01025/2026 são seis coligadas do Grupo Alupar; a controladora da plataforma é a ACE |
| Operadora (desenvolvimento) | ness. Processos e Tecnologia Ltda., CNPJ 72.027.097/0001-37 | Desenvolve a plataforma. O acesso a dado pessoal real fica restrito ao período de desenvolvimento e homologação (ADR 011) |
| Suboperador (infraestrutura) | Google Cloud | Processa o dado em `us-central1`, sob o DPA do contrato de nuvem da Alupar ([dpa.md](dpa.md)). A entidade contratante é a indicada nesse contrato |
| Encarregada | Rosimeire Miler dos Santos | Canal público: privacidade@alupar.com.br (art. 41, § 1º) |

As fontes de onde o dado é lido — Hubspot, CCEE, o Portal Alup hospedado na AWS
e os sistemas internos — são tratamentos já existentes da controladora e ficam
fora deste relatório. Ele cobre o que acontece a partir da leitura.

## b) Outras partes interessadas

- **Donos de dado por domínio** — a matriz RACI está pendente (A5). O dono do
  dado do Hubspot é o comercial da Alup, ainda sem nome.
- **Google** — participou da revisão arquitetural de 10/09 (G1); não foi
  consultado sobre este relatório.
- **Encarregada** — Rosimeire Miler dos Santos. **[ALUP]** parecer.

## c) Justificativa

A plataforma trata sobretudo dado de mercado e de operação. Dado pessoal
aparece em poucas fontes — o Hubspot e, quando o cliente é pessoa física, o
consumo por cliente da CCEE. Mesmo assim o RIPD se justifica:

1. **Legítimo interesse.** É a hipótese proposta para boa parte das operações
   (item g), e o art. 10, § 3º, prevê o relatório nesse caso.
2. **Transferência internacional.** Todo o ambiente fica em `us-central1`, nos
   Estados Unidos (ADR 011, art. 33).
3. **Tecnologia com IA generativa.** O Knowledge Catalog tem recursos com o
   modelo Gemini ativados (ADR 014), e o assistente do Dataform pode rascunhar
   descrições (ADR 012) — ele lê amostra real das tabelas.
4. **Dado ainda desconhecido.** As fontes da Onda 3 não têm schema; o relatório
   fixa os critérios antes de o dado chegar.

## d) Projeto que justifica o relatório

Plataforma AlupData: data lake em arquitetura *medallion* (Bronze, Silver, Gold)
no Google Cloud, que consolida 13 fontes de dado de mercado de energia, operação
e comercial em quatro ondas, para análise e indicadores da Alup. Contrato
CPS-01025/2026, de 27/08/2026 a 08/01/2027.

## e) Sistemas envolvidos

| Sistema | Papel | Onde |
|---|---|---|
| Projetos GCP `dev`, `hml` e `prod` | Três ambientes, pela resposta à pergunta E4. `prod` guarda o dado oficial; `dev` e `hml`, cópia com prazo curto | O `infra/` declara hoje `dev` e `prod`; o `hml` entra com a revisão da ADR 015, que previa dois |
| Cloud Storage, bucket `<projeto>-raw` | Guarda o registro bruto de cada leitura, antes de qualquer tratamento | `infra/modules/storage` |
| BigQuery: `bronze`, `silver`, `gold` | Camadas do lake; `qualidade` guarda linhas que falharam regra de qualidade | `infra/modules/bigquery` |
| Cloud Run Jobs | Executor dos conectores | `infra/` |
| Cloud Scheduler | Agenda as leituras | `infra/modules/scheduler` |
| Secret Manager | Credenciais das fontes | `infra/modules/secrets` |
| Dataform | Transformação Bronze → Silver → Gold | ADR 012 |
| Knowledge Catalog | Catálogo, linhagem e *profiling* | ADR 014 — ainda fora do Terraform |
| Cloud Logging | Logs de execução, 30 dias; log de auditoria de acesso a dados, 1 ano pela política de retenção | padrão do serviço; bucket de log dedicado a declarar |
| Portal (Cloud Run + IAP) | Consulta das tabelas Gold, saúde e custo | `infra/modules/portal`, com conta de serviço própria (ADR 005) |

A região é `us-central1` (ADR 023, que substituiu a 011 em 23/09), já
declarada em `infra/`.

**Classificação da informação (pergunta F4).** Os datasets e o bucket raw são
classificados como **internos**. O conteúdo confidencial listado no item f.ii
fica dentro desses datasets, protegido pelo controle de acesso por tipo de
usuário (item k, R01).

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

### ii. Dados pessoais e confidenciais tratados

Na resposta à pergunta F1, a Alup apontou como sensíveis — neste relatório,
**confidenciais**; ver item f.iii — o CNPJ, o CPF, o endereço e o valor de
contrato do Hubspot, o consumo realizado por cliente extraído da CCEE e as
planilhas e os dados gerados internamente: premissas de GSF, preço e outras
variáveis calculadas pela Comercialização, e o balanço energético da empresa.

| Origem | Dado | Confidencial (pergunta F1) | Dado pessoal? | Situação |
|---|---|---|---|---|
| Hubspot — negócios (A9) | `nome` do negócio — texto livre | Sim | Pode conter nome de pessoa física | **Lido hoje** (`dealname`) |
| Hubspot — negócios (A9) | `valor` do negócio — valor de contrato | Sim | Quando o negócio identifica uma pessoa física | **Lido hoje** (`amount`) |
| Hubspot — negócios (A9) | `proprietario_id` — usuário do Hubspot dono do negócio | — | Sim | **Retirado do conector** por decisão de 11/09 (item g) — PR #116 |
| Hubspot — empresas | CNPJ e endereço | Sim | Em regra, não: identificam pessoa jurídica. Exceção: empresário individual, em que CNPJ e endereço remetem a uma pessoa física | **Fora do escopo**, por decisão da Alup em 11/09 |
| Hubspot — contatos | CPF, endereço e demais dados do contato | Sim | Sim | **Fora do escopo**, por decisão da Alup em 11/09: o CPF não é tratado |
| CCEE | Consumo realizado por cliente | Sim | Quando o cliente é pessoa física | **Sem conector.** A fonte exata — CCEE com credencial de agente (plano, item 2.1) ou InfoMercado (item 1.1) — está a definir |
| Planilhas e dados internos (Ondas 3 e 4) | Premissas de GSF, preço e outras variáveis da Comercialização; balanço energético | Sim | A resposta à pergunta F1 não aponta dado pessoal | **Sem conector nem schema** (A4) |
| Usuários da plataforma | E-mail corporativo de quem acessa o Portal, recebido do IAP e exibido na tela | — | Sim | Confirmado no código (`src/portal/app.py`) |
| Usuários da plataforma | E-mail de quem executa consultas, nos logs de *jobs* do BigQuery; lido pelo Knowledge Catalog (ADR 014). A view `gold.custo_consultas` não o seleciona | — | Sim | Característica do serviço |
| Portal Alup (Onda 3) | **Desconhecido** — possivelmente dado de clientes | — | — | **[ALUP]** pergunta C6 |
| FMB, MySQL Comercialização, RM/TOTVS, SQL Server do Balanço (Onda 3) | **Desconhecido**. A resposta à pergunta F1 não aponta dado pessoal; os dados da Comercialização e o balanço são confidenciais | Em parte | — | Schema pendente |
| Fontes públicas (BCB, IBGE, ONS, ANEEL, CCEE pública) e de mercado licenciadas (BBCE, TempoOK) | Nenhum. A ANEEL SIGA lê só dados do empreendimento. O `ccee_perfil` traz CNPJ e razão social de ~60,5 mil perfis — identificador de empresa, não de pessoa natural | Não | Não | **Verificado em 14/09 contra o retrato de 01/09**: nenhum documento de 11 dígitos entre os 60.509; as 129 ocorrências de EIRELI/ME são pessoas jurídicas. A asserção `LENGTH(cnpj) = 14` reprova a carga se um CPF entrar (issue #110) |

**O conector do Hubspot lê só negócios.** Ele lê o objeto `deals`, com sete
propriedades — sem contatos, sem empresas e, desde a decisão de 11/09, sem o
dono do negócio. CPF e endereço ficam nos objetos de contato e de empresa: a
resposta à pergunta F1 descreve o que o Hubspot da Alup contém, não o que a
plataforma lê hoje. **Contatos e empresas do Hubspot ficam fora do escopo**,
por decisão da Alup em 11/09: o que não é lido não faz parte do escopo. CPF e
endereço, portanto, não são tratados. Ampliar esse escopo seria escopo novo, e
este relatório e o RoPA seriam revistos antes do conector, pela medida de R06.

### iii. Dados sensíveis

**Nenhum identificado no sentido do art. 5º, II, da LGPD.** A lei reserva
"dado pessoal sensível" a uma lista fechada — origem racial ou étnica,
convicção religiosa, opinião política, filiação a sindicato ou a organização de
caráter religioso, filosófico ou político, dado referente à saúde ou à vida
sexual, dado genético ou biométrico —, com hipóteses de tratamento próprias e
mais restritas (art. 11).

O que a Alup chamou de sensível na resposta à pergunta F1 é informação de
**sigilo corporativo**: dado de cliente, valor de contrato, consumo e cálculos
internos. Para não misturar os dois regimes, este relatório usa **confidencial**
para esse conjunto e guarda "sensível" para o sentido legal. A distinção não
reduz a proteção: o conjunto confidencial tem controle de acesso por tipo de
usuário como requisito (item k, R01). Dentro dele, CPF e endereço de pessoa
física são dado pessoal (art. 5º, I) e seguem a LGPD integralmente.

Ponto de atenção: o RM/TOTVS é um ERP e pode ter módulos de recursos humanos e
folha, que costumam conter dado sensível no sentido legal. Ver R06.

### iv. Categorias de titulares

- Colaboradores da Alup usuários do Portal e do BigQuery.
- Pessoas físicas eventualmente citadas no nome livre de um negócio, ou partes
  de um negócio.
- Clientes pessoa física da comercializadora, pelo consumo realizado (CCEE).
- Contatos do Hubspot, se o escopo for ampliado.
- **[ALUP]** Titulares do Portal Alup e dos sistemas internos.

### v. Titulares vulneráveis

Nenhum previsto. **[ALUP]** confirmar no Portal Alup.

### vi. Volume

- Hubspot: desconhecido; o conector ainda não rodou contra a conta real (A9).
- Consumo por cliente: desconhecido; depende da fonte na CCEE.
- Portal Alup, estimativa da reunião de 10/09: 2 GB no Aurora, 3 GB no
  DynamoDB, cerca de 8 GB no S3.
- FMB: desconhecido (C6).
- **[ALUP]** Número de titulares.

### vii. Fonte

Indireta: sistemas e serviços da própria controladora e a CCEE, da qual a Alup
é agente.

### viii. Finalidade

Quatro finalidades, detalhadas no [RoPA](ropa.md):

- **F1** — análise do desempenho comercial (OP-01);
- **F2** — controle de acesso e segurança da plataforma (OP-02);
- **F3** — governança: catálogo, linhagem e perfil dos dados (OP-03);
- **F4** — gestão da carteira de clientes: consumo realizado por cliente
  (OP-07), quando o conector existir.

As fontes da Onda 3 e as planilhas ganham finalidade própria quando o schema
for conhecido (OP-04 a OP-06).

### ix. Compartilhamento

- Google Cloud, como suboperador de infraestrutura.
- ness., como operadora, durante o desenvolvimento e a homologação.
- Nenhum outro destinatário. A ferramenta de BI ainda não foi definida (A6);
  quando for, este relatório é revisto.

### x. Armazenamento, retenção e transferência internacional

**Hoje** nada é excluído: o bucket raw só muda de classe aos 90 dias, o
versionamento guarda cópias antigas e o BigQuery não tem expiração.

A [política de retenção](politica-de-retencao.md), versão 0.2, incorpora os
critérios da Alup de 11/09 (perguntas F3 e G5):

- **mínimo de 5 anos para todos os dados, contados a partir de 2027** — a
  primeira carga traz todo o histórico, e o prazo dele também começa em 2027;
- **consumo por cliente**: 5 anos na Bronze e 10 anos na Gold mensal;
- **públicos pesados** (geração horária e *curtailment* semi-horário por usina
  do SIN): a partir do 6º ano, só a Gold mensal;
- **demais públicos**: sem expiração;
- **raw**: recomendação de manter pelo prazo da Bronze, em classe fria;
- **`dev` e `hml`**: 30 e 90 dias; **log de auditoria**: 1 ano.

Os prazos passam a valer quando aprovados formalmente e declarados no
repositório; os de 5 e 10 anos são ativados na primeira data de vencimento,
01/01/2032 e 01/01/2037.

**Transferência internacional (art. 33).** Todo o dado, nos três projetos, fica
em `us-central1`. A transferência se apoia no DPA do contrato de nuvem da Alupar;
o [registro do DPA](dpa.md) detalha o mecanismo.

## g) Hipótese legal

Análise proposta pela ness. **[ALUP]** Validação do jurídico e da encarregada.

| Finalidade | Dado | Titular | Hipótese proposta |
|---|---|---|---|
| F1 | `proprietario_id` | Colaborador dono do negócio | Não se aplica: retirado do conector em 11/09 |
| F1 | `nome` e `valor` do negócio | Pessoa física citada ou parte do negócio | Execução de contrato ou procedimentos preliminares (art. 7º, V), quando ela é parte do negócio; nos demais casos, legítimo interesse |
| F1 | CPF e endereço de contato do Hubspot | Contato pessoa física | **Não se aplica:** contatos e empresas ficam fora do escopo (decisão de 11/09). Refazer esta análise se algum dia entrarem |
| F2 | E-mail e registros de acesso e consulta | Usuário da plataforma | Legítimo interesse (art. 7º, IX) |
| F3 | Metadados e logs de consulta | Usuário da plataforma, indiretamente | Legítimo interesse (art. 7º, IX) |
| F4 | Consumo realizado por cliente | Cliente pessoa física | Execução de contrato (art. 7º, V): o consumo medido é o que se liquida no contrato de energia. **[ALUP]** confirmar, com o conector |

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
   ao domínio da Alup, retenção limitada (30 dias de log de execução e 1 ano
   de log de auditoria, pela política de retenção) e uso restrito à segurança.

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
| Finalidade e adequação | Finalidades F1 a F4 declaradas no RoPA | Onda 3 a definir |
| Necessidade | O Hubspot lê só 7 propriedades de negócios, sem contatos, empresas nem dono do negócio; a Gold não expõe o nome; dado sem prazo maior pedido pela Alup sai ao fim do mínimo de 5 anos | — |
| Livre acesso | Canal da encarregada, privacidade@alupar.com.br; eliminação a pedido na política de retenção | — |
| Qualidade | Validação na carga, deduplicação na Silver, *assertions* do Dataform | — |
| Transparência | Dicionário de dados, linhagem por fonte, este relatório e o RoPA | Aviso interno aos colaboradores (item g) |
| Segurança e prevenção | Ver item k. Por decisão da controladora (pergunta F2), não há mascaramento nem pseudonimização: a proteção é o **controle de acesso por tipo de usuário**, que passa a ser requisito | Controle por coluna e por linha e rótulo de classificação interna ainda a implementar (item k) |
| Não discriminação | Não há decisão automatizada sobre titulares | — |
| Responsabilização | Decisões em ADRs versionadas; histórico de commits | — |

## i) Riscos ao titular

| # | Risco |
|---|---|
| R01 | Acesso indevido a dado pessoal ou confidencial nos datasets e no Portal, por usuário cujo tipo não deveria vê-lo |
| R02 | Retenção indefinida: o bucket raw e o BigQuery não excluem nada, e a eliminação da cláusula 8.3 não tem procedimento |
| R03 | Transferência internacional sem mecanismo adequado |
| R04 | Dado pessoal em texto livre (nome do negócio) propagado da Bronze para a Silver e para o catálogo |
| R05 | Dado pessoal exposto a recursos de IA: o assistente do Dataform lê amostra real, e o Knowledge Catalog processa logs de consulta com e-mails |
| R06 | Dado pessoal ou sensível não previsto chegando por fonte ainda sem schema — Onda 3, consumo por cliente da CCEE — ou por ampliação futura de escopo |
| R07 | Rastreabilidade insuficiente de quem leu ou gravou dado pessoal |
| R08 | Acesso da ness. a dado real além do período de desenvolvimento e homologação |
| R09 | Vazamento de credencial de fonte, dando acesso ao dado na origem |
| R10 | Dado real de titular gravado no repositório de código |

## j) Avaliação

Metodologia: probabilidade (P) e impacto (I) de 1 a 3; nível = P × I. **Baixo**
de 1 a 2, **médio** de 3 a 4, **alto** de 6 a 9. Avaliação proposta pela ness.;
**[ALUP]** valida.

| # | P | I | Nível antes das medidas | Nível residual esperado |
|---|---|---|---|---|
| R01 | 2 | 3 | **Alto (6)** | Baixo, com o controle por tipo de usuário implementado (requisito da pergunta F2). Sem mascaramento, esse controle é a única barreira dentro dos datasets |
| R02 | 3 | 2 | **Alto (6)** | Baixo, com a política de retenção aprovada e declarada no repositório |
| R03 | 1 | 2 | Baixo (2) — há DPA | Baixo |
| R04 | 2 | 1 | Baixo (2) | Baixo |
| R05 | 2 | 2 | Médio (4) | Baixo |
| R06 | 2 | 3 | **Alto (6)** | Médio, até cada schema e o escopo do Hubspot serem conhecidos |
| R07 | 2 | 2 | Médio (4) | Baixo |
| R08 | 1 | 2 | Baixo (2) | Baixo |
| R09 | 1 | 3 | Médio (3) | Baixo |
| R10 | 1 | 1 | Baixo (1) | Baixo |

## k) Medidas, salvaguardas e mecanismos de mitigação

**E** = existe hoje · **R** = requisito da controladora, a implementar ·
**P** = proposta, a implementar. Tudo o que se implementa entra em `infra/` ou
no código (regra 5).

| # | Medida | Tipo |
|---|---|---|
| R01 | Contas de serviço com privilégio mínimo, verificado em teste (`tests/unit/test_infra.py`); Portal atrás do IAP, restrito ao domínio da Alup, que recusa requisição sem identidade | E |
| R01 | Acesso de pessoas por grupo, declarado em `infra/`: consumidores leem a Gold; Bronze e Silver só para quem opera. Nenhum acesso é concedido enquanto a Alup não indicar os grupos — PR #118 | E |
| R01 | IAP e serviço do Portal no Terraform, com conta de serviço própria — PR #118 | E |
| R01 | **Controle de acesso por tipo de usuário** (pergunta F2): um grupo por tipo de usuário; *policy tags* do BigQuery nas colunas confidenciais e com dado pessoal — nome e valor do negócio e consumo por cliente —, com leitura só para os tipos autorizados; políticas de acesso por linha onde o tipo de usuário exigir. Taxonomia, grupos e marcação das colunas declarados no repositório. **[ALUP]** tipos de usuário e o que cada um vê | R |
| R01 | Sem mascaramento nem pseudonimização (pergunta F2). Consequência operacional: quem não tem leitura na coluna protegida recebe erro ao consultar `SELECT *` e precisa excluir a coluna da consulta | R |
| R01 | Datasets e bucket raw rotulados como de classificação interna (pergunta F4), em `infra/` | R |
| R02 | Prazos da [política de retenção](politica-de-retencao.md) 0.2, pelos critérios das perguntas F3 e G5, declarados no repositório: ciclo de vida do bucket raw, expiração de partição na Bronze e na Gold de consumo, Gold mensal incremental protegida para os públicos pesados | R |
| R02 | Procedimento de eliminação a pedido do titular e da cláusula 8.3, no runbook | P |
| R03 | DPA do contrato de nuvem da Alupar ([dpa.md](dpa.md)) | E |
| R04 | A Gold não expõe `nome` nem `proprietario_id`: `funil_comercial` só agrega | E |
| R04 | Colunas com dado pessoal ou confidencial marcadas no catálogo e cobertas pela *policy tag* de R01 | R |
| R04 | `proprietario_id` retirado do conector, por decisão de 11/09 (item g) — PR #116 | E |
| R05 | O assistente do Dataform só entra por PR e não é apontado para tabela com dado pessoal (ADR 012); conteúdo gerado no catálogo fica `origem = automatica` e não homologa (ADR 014) | E |
| R05 | Manter o assistente fora das tabelas com colunas marcadas como pessoais ou confidenciais **também depois** da aprovação deste relatório | P |
| R06 | Antes de cada conector da Onda 3, do consumo por cliente e de qualquer ampliação do Hubspot: inventário de colunas com o dono do dado; seleção explícita de colunas e propriedades, nunca `SELECT *`; módulos de RH e folha fora do escopo de leitura; hipótese legal, prazo e *policy tag* definidos; revisão deste relatório e do RoPA | P |
| R07 | Log de auditoria de acesso a dados (*Data Access audit logs*) do BigQuery e do Cloud Storage, declarado em `infra/` — PR #118. O custo é da Alup | E |
| R07 | Retenção de 1 ano do log de auditoria, pela política de retenção: bucket de log dedicado e roteamento dos logs de acesso a dados, em `infra/`. Hoje valem os 30 dias padrão | R |
| R08 | Acesso da ness. por grupo nos três projetos, com revogação na homologação final e no handoff (cláusula 8.3); em `dev` e `hml`, dado com 30 e 90 dias | P |
| R09 | Credenciais só no Secret Manager; deploy via WIF, sem chave; gitleaks no CI e no pre-commit; teste que impede a senha de aparecer em mensagem de erro | E |
| R09 | Relatório de SAST/SCA do CI enviado semanalmente para alup.alertas@alupar.com.br (pergunta F5). Pendência operacional, ainda não implementada | P |
| R10 | Regra de não ter dado real no repositório (`AGENTS.md`, `SECURITY.md`); fixtures sintéticos | E |

## l) Comentários e aprovações

| Papel | Nome | Data | Parecer |
|---|---|---|---|
| Elaboração da minuta técnica | ness. | 11/09/2026 | Versão 0.6 |
| Encarregada | Rosimeire Miler dos Santos | | |
| Controladora | ACE Comercializadora Ltda. (Alup) | | |

---

## Pendências para fechar a versão 1.0

1. Validação das hipóteses legais e do teste de balanceamento (item g).
2. Aprovação formal da política de retenção 0.2, que já incorpora os critérios
   de 11/09 — incluindo a escolha do prazo do raw com dado pessoal (item f.x,
   R02).
3. Tipos de usuário e o que cada um acessa, para implementar o controle de
   acesso por tipo de usuário (pergunta F2; item k, R01).
4. Fonte do consumo por cliente na CCEE e confirmação da hipótese legal de F4
   (itens f.ii e g).
5. Dado pessoal do Portal Alup e das demais fontes da Onda 3 — pergunta C6
   (itens f.ii, R06).
6. Aviso interno de privacidade aos colaboradores (item g).
7. Validação da avaliação de risco (item j).
8. Entidade Google contratante e destinatário das notificações de
   subprocessador ([registro do DPA](dpa.md)).
9. Envio semanal do relatório de SAST/SCA do CI (pergunta F5; item k, R09).

## Histórico

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 11/09/2026 | Minuta técnica inicial, pela ness. |
| 0.2 | 11/09/2026 | Controladora e encarregada definidas; análise de hipótese legal com teste de balanceamento; política de retenção e DPA referenciados; R03 reavaliado |
| 0.3 | 11/09/2026 | Dados cadastrais da controladora (Receita Federal) e canal da encarregada; `proprietario_id` retirado do conector por decisão da Alup |
| 0.4 | 11/09/2026 | Medidas de R01, R04 e R07 passam a existentes, com a entrada dos PRs #116 e #118 na `main`; região e Portal descritos como estão no Terraform |
| 0.5 | 11/09/2026 | Respostas da Alup de 11/09 às perguntas F1 a F5, G5 e E4: dados confidenciais do Hubspot, da CCEE e internos, separando o que o conector lê hoje do que depende da confirmação de escopo; distinção entre sensível no sentido legal e confidencial; finalidade F4 (consumo por cliente); controle de acesso por tipo de usuário e *policy tags* passam a requisito; classificação interna; três ambientes; retenção pela política 0.2; envio do relatório de SAST/SCA como pendência |
| 0.6 | 11/09/2026 | Contatos e empresas do Hubspot ficam fora do escopo, por decisão da Alup: CPF e endereço não são tratados, e a pendência de escopo é encerrada |
| 0.7 | 14/09/2026 | Fontes públicas reconferidas contra o cadastro real da CCEE (`ccee_perfil`, 60.509 perfis): nenhum CPF, nenhuma pessoa natural. O controle que detecta a mudança é a asserção `LENGTH(cnpj) = 14` da Silver |
