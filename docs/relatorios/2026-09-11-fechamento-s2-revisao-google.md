---
titulo: Relatório de situação 11/09/2026 — AlupData Fase 1
documento: Relatório de situação
referencia: REL-2026-09-11 · AlupData Fase 1
emitido_em: 11 de setembro de 2026
emitente: ness. Processos e Tecnologia Ltda.
destinatario: Alup
contrato: CPS-01025/2026 — AlupData Fase 1: DataLake
marco: Onda 0 · 15,52% · R$ 23.040,00
responsavel: Ricardo Esper
classificacao: Confidencial — uso restrito das partes
local_data: 11 de setembro de 2026
---

# Fechamento da S2 e decisões da revisão arquitetural com o Google

## 1. Objeto

Registro da situação em 11/09/2026, último dia útil da semana S2
(07/09 – 11/09), abrangendo: o resultado da reunião de revisão arquitetural
com o Google, realizada em 10/09; as decisões de arquitetura que saíram dela; o
que elas mudam no pedido do ambiente GCP (insumo A3); a contagem de prazos; os
insumos com vencimento hoje; e o trabalho realizado na semana.

## 2. Revisão arquitetural com o Google — pendência G1 resolvida em 10/09

Agradecemos à Alup pela reunião de **10/09/2026** com o Google, que contou com
a participação das duas equipes. Com ela, a pendência **G1**
([issue #77](https://github.com/nessenergy/Alupdatalake/issues/77)) está
resolvida.

A espera pela reunião antes de criar o ambiente mostrou-se acertada: **a região
mudou**. Se o projeto já tivesse sido aplicado em São Paulo, a mudança agora
exigiria migrar dados, e não apenas ajustar configuração.

As decisões estão registradas em ADR, no
[PR #106](https://github.com/nessenergy/Alupdatalake/pull/106):

| Tema | Decisão | Registro |
|---|---|---|
| Região do ambiente | **`us-east1`** (Carolina do Sul), em `dev` e `prod`; substitui `southamerica-east1` | ADR 011 |
| Fundação do ambiente | **Três ambientes, `dev`, `hml` e `prod`**, com a homologação das ondas em `hml`; a Alup cria os projetos, os vincula ao faturamento (E1 e E2) e concede à ness. o papel para o bootstrap; **a ness. faz o bootstrap** — APIs, bucket de state, Artifact Registry e WIF — e constrói o restante da fundação em `infra/`; criptografia com chave gerenciada pelo Google, sem CMEK | ADR 015, revista em 11/09 |
| Transformação Silver e Gold | **Dataform**, com testes de dado e linhagem nativos; Gold de negócio materializada como tabela, Gold operacional em view | ADR 012, revista em 11/09 |
| Ingestão dos sistemas internos | **Em lote**, pelos conectores Python; sem CDC e sem Dataflow, porque o dado consumido é consolidado, não transacional | ADR 013 |
| Orquestração | Cloud Scheduler agora; **Airflow na Onda 3**, quando houver dependência entre pipelines | ADR 004, mantida |
| Governança | **Knowledge Catalog** na Onda 4, com linhagem desde o primeiro `apply`; recursos de IA generativa do próprio produto ativados sob aviso registrado | ADR 014 |
| Custo de nuvem | **Exportação do faturamento para o BigQuery** ligada no dia do primeiro `apply` | adendo à ADR 007 |

Duas consequências merecem atenção da Alup:

- **Transferência internacional de dado pessoal.** Com o ambiente nos EUA, o
  dado pessoal previsto (o nome livre dos negócios do Hubspot — os contatos não
  são lidos —, o e-mail de quem usa a plataforma e, possivelmente, dado do
  Portal Alup) passa a ser tratado fora do país. A transferência fica
  documentada em DPA, registro das operações de tratamento e relatório de
  impacto. Os dois últimos são documentos da controladora, a ACE
  Comercializadora Ltda., que tem como encarregada Rosimeire Miler dos Santos:
  a ness. entregou as minutas técnicas, em `docs/lgpd/`, para que o jurídico da
  Alup assuma e assine. Isso não bloqueia o primeiro `apply`.
- **A pergunta E7 do Questionário de Gaps**, sobre a região, fica respondida
  por esta decisão.

## 3. O pedido do ambiente GCP (A3), atualizado

Com a G1 resolvida, **A3 deixa de ter condicionante pendente**. A sequência
passa a ser:

    A3 (ambiente GCP) → 1º apply → Onda 0 homologada

As decisões acima alteram o que precisa ser provisionado. Pela ADR 015, revista
em 11/09 com as respostas E4 e E6 do Questionário de Gaps, são **três
ambientes — `dev`, `hml` e `prod` —**, cada um em um projeto: a Alup cria os
projetos, os vincula ao faturamento e concede à ness. o papel para o bootstrap
(item 1); **a ness. faz o bootstrap de cada projeto** (itens 3 a 5) e constrói
o restante em `infra/` — IAM, Dataform, linhagem, IAP do Portal e log de
auditoria de acesso a dados. A lista completa, atualizada, é esta:

| # | Item | Responsável |
|---|---|---|
| 1 | Projeto GCP `dev` criado na organização da Alupar, vinculado à conta de faturamento da Alup (E1 e E2, esclarecidos em 09/09) e com papel concedido à ness. no projeto para o bootstrap — os papéis estão listados na ADR 015; em seguida, da mesma forma, `hml` e `prod` | TI Alup |
| 2 | Política de localização da organização (`gcp.resourceLocations`) **permitindo `us-east1`** — se ela restringir recursos ao Brasil, o primeiro `apply` falha | TI Alup |
| 3 | APIs habilitadas: BigQuery, Cloud Storage, Secret Manager, Cloud Run, Cloud Scheduler, Artifact Registry **e, agora, Dataform, Data Lineage, Dataplex e Identity-Aware Proxy** | ness. |
| 4 | Bucket de state do Terraform e repositório do Artifact Registry **em `us-east1`** | ness. |
| 5 | Workload Identity Federation e service account de deploy, como já descrito na [issue #55](https://github.com/nessenergy/Alupdatalake/issues/55) | ness. |
| 6 | Uma pessoa com papel *Billing Account Costs Manager* (ou *Administrator*) na conta de faturamento **e** *BigQuery User* no projeto, para ligar a exportação do faturamento **no mesmo dia do primeiro `apply`** — dataset regional não recebe carga retroativa | Alup |
| 7 | Destinatários dos alertas (preferencialmente um grupo) e teto do orçamento — sugestão de R$ 500/mês em `dev`, conforme o [registro de 09/09](2026-09-09-esclarecimento-e1-e2.md) | Alup |
| 8 | Grupos Google da Alup que leem a Gold (consumidores) e as três camadas (operação), e quem acessa o Portal pelo IAP — não bloqueiam o primeiro `apply`: vazios, ninguém recebe acesso a dado (R01 do RIPD) | Alup |

Renovamos a proposta feita em 09/09: uma conversa de **30 minutos** com a
equipe de TI da Alup, em que o projeto seja criado e os acessos concedidos ao
vivo, com esta lista como roteiro.

## 4. Contagem de prazos — cláusula 3ª

| Marco | Data | Efeito |
|---|---|---|
| 1º dia útil de atraso de A3 | 08/09/2026 | contagem iniciada |
| 4º dia útil | **11/09/2026** (hoje) | contagem em curso |
| 5º dia útil | **14/09/2026** | postergação dos prazos dependentes de A3 |
| 20 dias corridos | **24/09/2026** | hipótese de suspensão dos serviços |

A resolução da G1 não altera a contagem, que considera o atraso do insumo e não
o seu motivo, como registrado em 04/09. O que ela altera é a previsão: A3 passa
a depender apenas do provisionamento descrito na seção 3.

## 5. Insumos com vencimento em 11/09/2026

Os cinco insumos abaixo vencem hoje e **não foram recebidos até a emissão deste
relatório**. Como 12 e 13 recaem sobre o fim de semana, o primeiro dia útil de
atraso será **14/09**.

| # | Insumo | Efeito da não disponibilização | Issue |
|---|---|---|---|
| A4 | Questionário de Gaps respondido (47 perguntas) | os 8 domínios analíticos não se definem; a camada Gold fica sem alvo | [#8](https://github.com/nessenergy/Alupdatalake/issues/8) |
| A9 | Token do Hubspot | conector concluído permanece sem execução | [#11](https://github.com/nessenergy/Alupdatalake/issues/11) |
| A5 | Matriz RACI e data owners | questões de regra de negócio sem destinatário definido | [#9](https://github.com/nessenergy/Alupdatalake/issues/9) |
| A6 | Ferramenta de BI definida | Portal MVP e camada Gold sem consumidor definido | [#10](https://github.com/nessenergy/Alupdatalake/issues/10) |
| — | Destinatários de alerta e teto do orçamento | alertas e orçamento configurados, sem destinatário | [#87](https://github.com/nessenergy/Alupdatalake/issues/87) |

Reiteramos o registro de 08/09: **A4 é o único destes insumos que não depende do
ambiente GCP**. Ainda que A3 chegue de imediato, sem as respostas do
questionário a semana S3 não tem escopo executável na camada Gold.

## 6. Trabalho da S2

O plano previa para esta semana o primeiro deploy real, que depende de A3 e
foi integralmente postergado. O tempo foi dedicado a registrar e implementar as
decisões da seção 2 **antes** do primeiro `apply` — enquanto mudar o desenho
ainda custa código, e não migração.

| PR | Conteúdo |
|---|---|
| [#106](https://github.com/nessenergy/Alupdatalake/pull/106) | ADRs 011 a 015, adendo à ADR 007 e minutas de LGPD em `docs/lgpd/`: RIPD, RoPA, política de retenção e registro do DPA |
| [#107](https://github.com/nessenergy/Alupdatalake/pull/107) | Ambiente em `us-east1`, destino da exportação do faturamento e roteiro do primeiro deploy |
| [#108](https://github.com/nessenergy/Alupdatalake/pull/108) | SQL das três camadas migrado para o Dataform, com conta de serviço própria; o deploy executa o Dataform logo após o `apply`, e a carga passa a recusar tabela inexistente, o que garante que toda tabela Bronze nasça particionada |
| [#109](https://github.com/nessenergy/Alupdatalake/pull/109) | Linhagem da origem até o Bronze registrada no Knowledge Catalog |
| [#116](https://github.com/nessenergy/Alupdatalake/pull/116) | Conector do Hubspot deixa de ler o dono do negócio (`proprietario_id`), dado pessoal que nenhuma tabela Gold usava |
| [#117](https://github.com/nessenergy/Alupdatalake/pull/117) | Gold de negócio materializada como tabela; a Gold operacional, que alimenta os painéis de saúde e de custo, segue em view |
| [#118](https://github.com/nessenergy/Alupdatalake/pull/118) | Medidas R01 e R07 do RIPD em `infra/`: acesso de pessoas por grupo, Portal atrás do IAP com conta de serviço própria e log de auditoria de acesso a dados do BigQuery e do Cloud Storage |
| [#119](https://github.com/nessenergy/Alupdatalake/pull/119) | RIPD 0.4, com as medidas de R01, R04 e R07 registradas como implementadas |

Os PRs foram integrados à `main` em 11/09. Cada um passou por revisão técnica
e pelas verificações automatizadas executadas localmente.

**Ressalva, mantida do registro de 08/09:** nenhuma entrega foi validada contra
ambiente GCP real, que ainda não existe, e nenhuma foi conferida pela Alup.
Entrega técnica não constitui homologação.

## 7. Solicitações

| # | Solicitação | Prazo | Issue |
|---|---|---|---|
| 1 | A3 — provisionamento do ambiente conforme a lista da seção 3 | **até 14/09**, 5º dia útil | [#55](https://github.com/nessenergy/Alupdatalake/issues/55) |
| 2 | A4 — Questionário de Gaps respondido, incluindo o registro por escrito da concordância com a região (E7) | imediato | [#8](https://github.com/nessenergy/Alupdatalake/issues/8) |
| 3 | A9, A5, A6 e destinatários de alerta, conforme a seção 5 | imediato | [#11](https://github.com/nessenergy/Alupdatalake/issues/11), [#9](https://github.com/nessenergy/Alupdatalake/issues/9), [#10](https://github.com/nessenergy/Alupdatalake/issues/10), [#87](https://github.com/nessenergy/Alupdatalake/issues/87) |
| 4 | Decisão sobre a CCEE — 32h da Onda 1 sem execução | 18/09 | [#52](https://github.com/nessenergy/Alupdatalake/issues/52) |
| 5 | Aceite por escrito de que o componente "View Gold" da cláusula 2.2 é atendido pela camada Gold materializada pelo Dataform (ADR 012) | antes da homologação da Onda 1 | — |
| 6 | Aprovação das minutas de LGPD em `docs/lgpd/` — RIPD, RoPA, política de retenção e registro do DPA — pela controladora e pela encarregada | a combinar | — |
| 7 | Itens marcados **[ALUP]** nas minutas de LGPD, como a validação das hipóteses legais, o dado pessoal do Portal Alup e das fontes da Onda 3 (C6 e F1) e a entidade Google contratante | com o item 6 | — |

Agradecemos, mais uma vez, o empenho da Alup em viabilizar a revisão com o
Google. Permanecemos à disposição para a conversa proposta na seção 3 e para
qualquer esclarecimento.

---

*Situação corrente em [`../status.md`](../status.md). Questões abertas
acompanhadas na [issue #57](https://github.com/nessenergy/Alupdatalake/issues/57).*
