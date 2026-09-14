# Questionário de Gaps — AlupData Fase 1

**Contrato** CPS-01025/2026 · **Onda 0** · dependência **A4** (cláusula 3ª)
**Emitido por** ness. Processos e Tecnologia · **Para** Grupo Alupar
**Data de emissão** 31/08/2026 · **Prazo de resposta** 11/09/2026
**Respondido em** 11/09/2026, por Taina Mota (Alup), dentro do prazo

---

## Situação das respostas

A Alup respondeu aos sete blocos em **11/09/2026**. A coluna **Resposta** traz
cada resposta resumida, com a data. Onde ela muda uma decisão já registrada, a
ADR afetada está citada. O que vem marcado **ness.** é observação nossa, não
resposta da Alup.

Continuam pendentes:

| # | O que falta | Prazo |
|---|---|---|
| C1 | Números dos chamados de token (Onda 2) e de acesso (Onda 3) | chamados abertos a partir de 14/09 |
| C4 | Orientação da Alup, pelo Google Chat, para ajustar a requisição à CCEE | sem data |
| C5 | Versão do Oracle FMB e existência de réplica de leitura | não informado |
| C7 | Forma de integração do RM/TOTVS e ambiente de homologação | 25/09 |
| E1 | Conta de faturamento, em acerto com a QI Network; nome do responsável não informado | 18/09 |
| G3 | Exemplos reais das planilhas | 18/09 |

---

## Como usar

48 perguntas em 7 blocos. Cada bloco tem um destinatário provável — a coluna
**Quem** é sugestão, não imposição; se o dono certo for outro, corrija.

Regras que tornam a resposta útil:

- **"Não sei" é resposta válida e desejada.** O objetivo é achar gaps, não
  parecer completo. Um "não sei, falar com o Fulano" vale mais que um chute.
- **"Não se aplica" também.** Diga por quê em uma linha.
- Perguntas marcadas **[BLOQUEIA]** travam trabalho que já está pago e parado.
  Se o bloco inteiro não puder ser respondido até 11/09, responda ao menos essas.
- Onde a pergunta pede uma data, precisamos de **data com responsável**, não de
  estimativa ("até 10/09, com o João" — não "início de setembro").

Devolver para: **resper@bekaa.eu**, ou como comentário na
[issue #8](https://github.com/nessenergy/Alupdatalake/issues/8).

---

## Bloco A — Domínios analíticos e prioridade (7)

O contrato prevê 8 domínios analíticos (cláusula 4ª, Onda 0). Eles ainda não
foram definidos. Sem isso, a camada Gold — que é o que a Alup efetivamente
consome — não tem alvo.

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| A1 | **[BLOQUEIA]** Quais são as 8 perguntas de negócio que este DataLake precisa responder no primeiro ano? Enumere em linguagem de negócio, não de sistema. | Diretoria / Comercial | **11/09**: (1) base única e integrada; (2) automação de processos operacionais; (3) relatórios e dashboards atualizados, quase em tempo real; (4) qualidade e rastreabilidade do dado; (5) decisão orientada por dados; (6) escalar o negócio; (7) novos produtos, serviços e negócios; (8) base preparada para IA no futuro. **ness.**: a ingestão é em lote, por janela ([ADR 013](arquitetura/decisoes/013-ingestao-em-lote.md)), e os sistemas internos só podem ser lidos das 22h às 6h (C9). "Quase em tempo real" precisa virar frequência por fonte — para os sistemas internos, no máximo diária. |
| A2 | **[BLOQUEIA]** Dessas 8, quais 3 dão retorno mais rápido se entregues primeiro? | Diretoria | **11/09**: os itens 1, 2 e 3 de A1 — base única e integrada, automação de processos operacionais, e relatórios e dashboards atualizados. |
| A3 | Hoje, essas perguntas são respondidas como? (planilha, relatório manual, sistema, ninguém responde) | Comercial / Controladoria | **11/09**: parte em bancos automatizados que alimentam dashboards da área; parte em planilhas, que combinam banco automatizado e entradas manuais, enviadas como reports à diretoria e à presidência. |
| A4 | Quem consome cada resposta e com que frequência (diária, semanal, mensal, sob demanda)? | Cada área | **11/09**: a Comercialização consome diariamente; a diretoria e a presidência, semanal ou mensalmente, em reuniões, e sob demanda nos dashboards. |
| A5 | Existe algum indicador/KPI já formalizado e com fórmula acordada entre as 6 coligadas? Se sim, envie a definição. | Controladoria | **11/09**: não existem KPIs formalizados, e defini-los não é objetivo desta fase. O objetivo agora é ter os dados organizados e a estrutura do datalake funcionando; os indicadores serão definidos no projeto de front (Fase 2). Muda a Gold desta fase: [ADR 012, "Gold na Fase 1"](arquitetura/decisoes/012-dataform.md#gold-na-fase-1). |
| A6 | Há métrica que hoje é calculada de formas diferentes por coligada? Qual, e qual versão vale? | Controladoria | **11/09**: mesma resposta de A5 — sem KPI formalizado nesta fase, não há versão de métrica a arbitrar agora. Fica para a Fase 2. |
| A7 | Qual granularidade mínima é aceitável para decisão: usina, coligada, submercado, grupo? | Comercial | **11/09**: depende do dado. Usina, quando o dado é do portfólio; usina, estado ou submercado, quando é do SIN. Adotada como granularidade da Gold ([ADR 012](arquitetura/decisoes/012-dataform.md#gold-na-fase-1)). **Não confundir com o A7 do painel de dependências** ([`status.md`](status.md) §6), que é a abertura dos pedidos de token e VPN: mesma sigla, outro assunto. |

---

## Bloco B — Donos de dados e governança (6)

Dependência **A5** (matriz RACI). Sem dono, dúvida de regra de negócio não tem
para quem ir, e a ness. para de trabalhar esperando resposta.

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| B1 | **[BLOQUEIA]** Quem é o **data owner** de cada domínio definido no bloco A? Nome, área e e-mail. | Diretoria | **11/09**: respondido por domínio de dado — quadro logo abaixo desta tabela. Os e-mails corporativos vieram na resposta e não se repetem aqui; o contato fica em [`interlocutores.md`](interlocutores.md). |
| B2 | **[BLOQUEIA]** Quem é o ponto focal técnico da Alup para desbloqueio de acesso (VPN, credencial, firewall)? Nome e substituto. | TI | **11/09**: Leonardo Marques; substituto, Mauricio Cardoso. |
| B3 | Qual o SLA interno da Alup para responder uma dúvida de regra de negócio? | Diretoria | **11/09**: até 3 dias úteis. |
| B4 | Quem aprova formalmente a homologação de cada onda e assina a medição? | Diretoria / Compras | **11/09**: Taina Mota. |
| B5 | Existe comitê ou fórum recorrente onde o projeto será acompanhado? Data e participantes. | PMO | **11/09**: sim — reuniões às sextas-feiras, com a Comercialização e o time técnico da ness. |
| B6 | Há política de governança de dados já escrita na Alup (classificação, qualidade, retenção)? Envie. | Compliance | **11/09**: não há política escrita. A Alup entende que a ness. será responsável por garantir a governança e a auditoria de mudanças nos dados. **Posição da ness.**: entregamos a governança configurada — catálogo, linhagem, qualidade e trilha de auditoria, na Onda 4 ([ADR 014](arquitetura/decisoes/014-knowledge-catalog.md)) — e a sua documentação. A operação contínua depois do handoff é da Alup; sustentação está fora do escopo desta fase (cláusulas 9ª e 10ª, sustentação opcional e contratada à parte). |

### Resposta ao B1 — data owners por domínio

**São 8 domínios em 11 linhas.** Um domínio aparece em mais de uma linha quando
responsáveis distintos tratam subtemas dele — é o caso de Mercado de Energia,
Geração e Operacional e Comercial e Contratos. Este quadro, e não o A1, é a
definição dos domínios analíticos que a Gold persegue
([`arquitetura/dominios-analiticos.md`](arquitetura/dominios-analiticos.md)).

| Domínio | Data owner | Área |
|---|---|---|
| Mercado de Energia — PLD, EAR, ENA, CCEE (CVU, ESS, EER), ONS (carga, térmicas, geração) | Taina Mota | Inteligência de Mercado |
| Mercado de Energia — BBCE e prêmio | Gabriel Barreto | Trading |
| Geração e Operacional — usinas do SIN e DESSEM | Taina Mota | Inteligência de Mercado |
| Geração e Operacional — usinas da Alupar e medição | Letícia Ferreira | Gestão de Portfólio e Back-Office |
| Meteorologia — precipitação, vento, clima | Taina Mota | Inteligência de Mercado |
| Comercial e Contratos — book, sazonalização, garantias | Letícia Ferreira | Gestão de Portfólio e Back-Office |
| Comercial e Contratos — contratos de varejo e Hubspot | Tahigo Santos | Comercial |
| CRM e Marketing — leads, campanhas, documentos | Tahigo Santos | Comercial |
| Risco e Compliance — exposição, GSF, Proinfa | Letícia Ferreira | Gestão de Portfólio e Back-Office |
| Econômico — IPCA, Selic, câmbio, CDI | Letícia Ferreira | Gestão de Portfólio e Back-Office |
| Planejamento — orçamento, premissas | gestores da Comercialização: Letícia Ferreira, Tahigo Santos e Taina Mota | Comercialização |

---

## Bloco C — Fontes e sistemas internos (11)

Ondas 2 e 3. **A7** é o maior risco financeiro do contrato: atraso > 5 dias
úteis em VPN/credencial dispara ociosidade de 4h/dia (R$ 256/h, cláusula 3ª).

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| C1 | **[BLOQUEIA]** Os pedidos internos de token (Onda 2) e VPN/credencial read-only (Onda 3) já foram **abertos**? Envie os números de chamado. | TI | **11/09**: ainda não foram abertos; serão a partir de 14/09. **Pendente**: os números de chamado. |
| C2 | **[BLOQUEIA]** Qual o prazo real do processo interno de liberação de acesso a banco de produção, do pedido à credencial na mão? | TI / Segurança | **11/09**: o banco de produção da Comercialização é liberado assim que solicitado. |
| C3 | **[BLOQUEIA]** A Alup consegue fornecer a **documentação técnica de BBCE e TempoOK** (contratos de API, manuais do fornecedor)? Ela vale tanto quanto o token e pode vir antes. | Comercial | **11/09**: sim. A documentação da API BBCE está no Postman. O TempoOK não tem documentação. **ness.**: sem documentação, o contrato de dados do TempoOK só se escreve com o token na mão. |
| C4 | **[BLOQUEIA]** CCEE InfoMercado responde 403 a acesso automatizado. Qual caminho a Alup escolhe: (a) liberar IP junto à CCEE, (b) fornecer credencial de agente, (c) **ler do SQL Server que já recebe o Balanço Energético** — ver adendo abaixo, (d) remanejar as 32h para outro escopo? | Comercial | **11/09**: InfoMercado e Balanço Energético são dados diferentes, os dois da CCEE. **InfoMercado**: é público (dados abertos da CCEE); o 403 se resolve ajustando a requisição, e a Alup vai orientar o ajuste pelo Google Chat. Nenhuma das vias (a) a (d) é necessária. **Balanço Energético**: não está mais no SQL Server; está no MySQL RDS na AWS, alimentado por automação sob demanda (C11). **Pendente**: a orientação do ajuste. |
| C5 | Oracle FMB: versão, host, porta, nome do schema, e existe réplica de leitura? | TI | **11/09**: acesso somente às views. Host, porta e schema foram recebidos em 11/09 e ficam fora do repositório, na DSN do Secret Manager (regra 2, [ADR 008](arquitetura/decisoes/008-acesso-a-bancos-relacionais.md)). **Pendente**: versão e réplica de leitura, não informadas. O caminho de rede segue a confirmar ([ADR 013](arquitetura/decisoes/013-ingestao-em-lote.md)). |
| C6 | Portal Alup: quais bases exatamente (MySQL, NoSQL, Storage), e qual o volume aproximado de cada uma? | TI | **11/09**: Aurora, cerca de 2 GB; DynamoDB, cerca de 3 GB; S3, cerca de 7,8 GB; MySQL, cerca de 36 GB (50 GB alocados). **ness.**: DynamoDB e S3 não são bancos relacionais e ficam fora do caminho da ADR 008; o Aurora depende do motor (compatível com MySQL ou com PostgreSQL). Confirma-se com o acesso. |
| C7 | RM/TOTVS: a integração será por API, view de banco ou exportação? Existe ambiente de homologação? | TI | **Pendente até 25/09.** |
| C8 | MySQL RDS Comercialização: está em qual nuvem/região, e há peering ou precisa de VPN? | TI | **11/09**: AWS, Norte da Virgínia (`us-east-1`). Não precisa de peering nem de VPN; o acesso será dado pelo Leonardo. Muda a rede da Onda 3: [revisão de 11/09 da ADR 013](arquitetura/decisoes/013-ingestao-em-lote.md). |
| C9 | Para cada sistema interno: qual a janela em que a extração pode rodar sem impactar a operação? | TI | **11/09**: das 22h às 6h ([ADR 013](arquitetura/decisoes/013-ingestao-em-lote.md)). |
| C10 | Há alguma fonte relevante que **não** está na lista do contrato e deveria estar? | Todas as áreas | **11/09**: nenhuma por ora. |
| C11 | **SQL Server do Balanço Energético** (ver adendo): host, instância, base, tabela e versão do SQL Server; quem administra; qual o histórico disponível; e a carga do Leonardo grava tudo ou só o mês corrente? | TI / Comercial | **11/09**: o SQL Server não será usado; houve migração para a AWS. O Balanço Energético está no MySQL RDS (C4). Adendo de 11/09 à [ADR 008](arquitetura/decisoes/008-acesso-a-bancos-relacionais.md). **ness.**: as perguntas de tabela e de histórico passam a valer para o MySQL RDS e se respondem com o acesso (C8). |

### Adendo ao C4 — o SQL Server do Balanço Energético

A Alup informou que já mantém um **SQL Server com o realizado do Balanço
Energético vindo da CCEE**, alimentado por um processo mensal manual conduzido
pelo Leonardo. A informação foi passada como contexto, sem pedido de inclusão
no escopo.

Registramos aqui porque ela **muda o C4**, em três pontos:

1. **Abre uma alternativa que não existia.** As opções originais supunham que a
   única via para o dado da CCEE era o portal, hoje bloqueado por 403. Se o
   Balanço Energético que a Alup precisa já está nesse SQL Server, ler dali
   pode entregar o resultado sem depender de liberação da CCEE — e as 32h
   deixam de ser candidatas a remanejamento.

2. **Pode destravar a dimensão `agente_ccee`.** É uma das cinco dimensões
   comuns da camada Silver e hoje é a única **sem fonte definida**, justamente
   por depender do desbloqueio da CCEE. Se a tabela do Balanço carrega o código
   do agente, a dimensão passa a ter origem.

3. **Envolve um banco que o projeto ainda não acessa.** O framework fala Oracle
   e MySQL; SQL Server exigiria um driver adicional. É trabalho pequeno, mas
   precisa ser dimensionado antes de a opção (c) ser escolhida, não depois.

**Se a automação não for feita**, fica registrado que o dado continua sendo
coletado mensalmente pelo processo manual do Leonardo. Isso é uma dependência
de pessoa: o dado do Balanço Energético passa a ter frequência, prazo e
qualidade atrelados à disponibilidade de uma pessoa, sem alerta se falhar.
Aceitável como decisão consciente — mas precisa ser decisão, não omissão.

**Atualização de 11/09.** As respostas ao C4 e ao C11 superam este adendo. O
SQL Server foi descontinuado; o Balanço Energético está no MySQL RDS na AWS,
alimentado por automação sob demanda, e é um dado diferente do InfoMercado — a
via (c) deixa de ser alternativa ao portal da CCEE. Dos três pontos acima:

1. as 32h do InfoMercado continuam no escopo, pela via pública, com a
   requisição ajustada;
2. a origem de `agente_ccee` passa a depender de a tabela do Balanço no MySQL
   RDS trazer o código do agente;
3. o driver adicional não é mais necessário: o MySQL já é suportado.

A dependência de pessoa diminui com a automação, mas "sob demanda" ainda
significa que alguém dispara a carga.

---

## Bloco D — Regras de negócio e camada Gold (7)

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| D1 | Como se identifica uma usina de forma única entre os sistemas? O CodCEG da ANEEL serve como chave, ou há código interno? | Engenharia | **11/09**: siglas internas identificam as empresas — FGE, FOZ, IJU, QLZ, LVR, VD8, EAP I, EAP II, PTB, EDV I a IV e X, ALP e ALUP. O CEG não é usado hoje, mas pode ser avaliado. A CCEE e o ONS usam nomes diferentes para os conjuntos de usinas. **ness.**: a dimensão de usina precisa de um de-para entre sigla, CEG, nome CCEE e nome ONS. |
| D2 | Qual o código de agente CCEE de cada uma das 6 coligadas? | Comercial | **11/09**: não são só 6 coligadas — são todos os ativos e também os clientes varejistas. Os códigos estão nos bancos da Alup, e a Alup vai mostrar scripts de referência. **Precisão de 14/09**: as 6 coligadas respondem pelo faturamento do contrato e **não delimitam o dado**. O escopo de dado é o mapeado na planilha da proposta, desde antes dela — usinas pela **CCEE**, varejo pelo **Portal Alup** —, e tudo isso é **Fase 1** ([`arquitetura/dominios-analiticos.md`](arquitetura/dominios-analiticos.md), §2). |
| D3 | Uma usina pode mudar de coligada ao longo do tempo? Se sim, o histórico deve seguir a usina ou a coligada? | Controladoria | **11/09**: não; os ativos não mudam de coligada. |
| D4 | Qual o calendário de apuração que vale: mês civil, mês CCEE, ou ambos? | Controladoria | **11/09**: os dois calendários. |
| D5 | Como tratar retificação de dado já publicado (ex.: CCEE recontabiliza mês fechado) — sobrescrever ou versionar? | Controladoria | **11/09**: versionar, para rastrear as recontabilizações da CCEE. Proposta de modelo em [ADR 016](arquitetura/decisoes/016-versionamento-de-recontabilizacao.md). |
| D6 | Quais conversões de unidade e moeda são obrigatórias (MWh/MWm, R$/US$) e qual a fonte oficial da taxa? | Controladoria | **11/09**: energia em MWh e MWmed; valores em R$, milhares de R$ ou milhões de R$. A resposta não cita conversão para US$. Aplicado na Gold ([ADR 012](arquitetura/decisoes/012-dataform.md#gold-na-fase-1)). |
| D7 | Há regra de arredondamento ou truncamento que a Alup exige em valor financeiro? | Controladoria | **11/09**: R$/MWh com duas casas decimais. Aplicado na Gold ([ADR 012](arquitetura/decisoes/012-dataform.md#gold-na-fase-1)). |

---

## Bloco E — Ambiente GCP e acessos (7)

Dependência **A3**, prazo **04/09**. É a mais urgente: nada sobe sem ela, e a
Onda 0 não homologa. Todo o cronograma pendura nesta linha.

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| E1 | **[BLOQUEIA]** Qual a **data e o responsável** pela criação do projeto GCP `dev`? Precisamos de data com nome, não de estimativa. | TI | **Atribuição esclarecida em 09/09**: a criação cabe à Alup, administradora da organização GCP — a ness. não tem, e não deve ter, permissão de criar projeto na organização da contratante ([issue #55](https://github.com/nessenergy/Alupdatalake/issues/55), [registro de 09/09](relatorios/2026-09-09-esclarecimento-e1-e2.md)). **11/09**: o faturamento está em acerto com a QI Network, com previsão para 18/09. **Pendente até 18/09**; o nome do responsável não consta da resposta. |
| E2 | **[BLOQUEIA]** Qual a `billing_account` a ser vinculada, e qual o teto mensal de custo aceitável para o alerta de orçamento? | Controladoria / TI | **Atribuição esclarecida em 09/09**: a conta é da Alup — a cláusula 5ª exclui do escopo da ness. os custos de infraestrutura GCP ([issue #87](https://github.com/nessenergy/Alupdatalake/issues/87)). **11/09**: conta Google da Alupar, com medição e pagamento por coligada. Teto de US$ 20/mês até novembro e de até US$ 400/mês a partir de meados de novembro. **ness.**: o teto a partir de novembro fica abaixo da estimativa de US$ 420–500/mês com orquestração gerenciada, apresentada no registro de 09/09. |
| E3 | **[BLOQUEIA]** Quem recebe os alertas de falha de ingestão? Envie e-mails ou canal (a infraestrutura de alerta existe e está sem destinatário). | TI | **11/09**: `alup.alertas@alupar.com.br`. |
| E4 | A Alup provisiona também o projeto de **produção** agora, ou só `dev` nesta fase? | TI | **11/09**: três ambientes — desenvolvimento, homologação e produção. Decisão da ness. de 11/09: adotar os três. Muda a [ADR 015](arquitetura/decisoes/015-fundacao-do-ambiente.md), que previa só `dev` e `prod`. |
| E5 | Existe organização/pasta GCP e política de nomenclatura corporativa que devemos seguir? | TI | **11/09**: não há organização nem política de nomenclatura. |
| E6 | Quem administra o Workload Identity Federation para o deploy via GitHub Actions? | TI | **11/09**: a ness. Decisão da ness. de 11/09: o bootstrap do ambiente fica com a ness. Muda a [ADR 015](arquitetura/decisoes/015-fundacao-do-ambiente.md), que o atribuía à Alup. |
| E7 | Há restrição de região? Assumimos `southamerica-east1` (São Paulo) — confirma? | TI | **11/09**: região nos EUA, com bom custo-benefício. Coerente com a decisão de 10/09 por `us-east1` ([ADR 011](arquitetura/decisoes/011-regiao-us-east1.md)). |

---

## Bloco F — Segurança, LGPD e retenção (5)

Cláusula 8ª. Perguntas cuja resposta muda o desenho, não só a operação.

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| F1 | Alguma das fontes contém **dado pessoal** (CPF, nome, contato — o Hubspot muito provavelmente sim)? Quais campos? | Compliance / DPO | **11/09**: sim. O Hubspot tem dados sensíveis: CNPJ, CPF, endereço e valor de contrato. Também são confidenciais o consumo por cliente, vindo da CCEE, e as planilhas e dados internos (premissas de GSF, preço, balanço energético). **Complemento de 11/09**: contatos e empresas do Hubspot ficam **fora do escopo** — o que não é lido não faz parte do escopo —, e o CPF não é tratado. Tratamento em [`lgpd/`](lgpd/ripd.md). |
| F2 | Se sim, qual a base legal e o tratamento exigido: mascarar, pseudonimizar, ou restringir acesso por IAM? | DPO | **11/09**: não aplicar tratamento (mascaramento ou pseudonimização); restringir o acesso por tipo de usuário. |
| F3 | Qual a política de retenção por camada (Bronze bruto, Silver, Gold)? Há obrigação regulatória de guardar por N anos? | Compliance | **11/09**: respondida; detalhe na [política de retenção](lgpd/politica-de-retencao.md). A retenção conta a partir de 2027 (G5). |
| F4 | Há classificação de informação corporativa (público/interno/confidencial) que devemos aplicar aos datasets? | Segurança | **11/09**: datasets classificados como internos. |
| F5 | O relatório de SAST/SCA do CI precisa ser enviado a alguma área da Alup periodicamente? Para quem e com que frequência? | Segurança | **11/09**: sim — semanal, para `alup.alertas@alupar.com.br`. |

---

## Bloco G — Consumo, BI e planilhas (5)

Dependências **A6** (BI) e insumo do motor S2 Data Intake da Onda 4.

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| G1 | **[BLOQUEIA]** Qual a ferramenta de BI definitiva: Power BI, Looker Studio, Tableau, outra? A escolha muda o formato de entrega das views Gold. | TI / Diretoria | **11/09**: hoje, Power BI e fronts internos; na Fase 2, Looker Studio ou fronts internos. |
| G2 | Já existem licenças contratadas dessa ferramenta, e quantos usuários? | TI | **11/09**: 9 licenças de Power BI. |
| G3 | Quais planilhas hoje alimentam decisão e deveriam entrar pelo S2 Data Intake? Envie exemplos reais dos arquivos. | Cada área | **11/09**: exemplos reais até 18/09. **Pendente até 18/09.** **ness.**: o prazo não atrasa as ondas — os templates de planilha são o item 4.1 da Onda 4, e o motor S2 Data Intake já está pronto. |
| G4 | Quem mantém cada planilha, e com que periodicidade ela é atualizada? | Cada área | **11/09**: consta na planilha (Google Sheets) da proposta. |
| G5 | Qual profundidade de histórico é necessária na primeira carga (ex.: ONS desde 2018 ou só 2026)? Isso tem impacto direto em custo de BigQuery. | Controladoria | **11/09**: primeira carga com todo o histórico; a retenção passa a contar a partir de 2027. |

---

## Efeito contratual de não responder

Registrado aqui porque a cláusula 3ª exige que a data do pedido conste do dia em
que o atraso começa, não do dia em que vira problema.

| Situação | Efeito |
|---|---|
| Atraso > 5 dias úteis em qualquer insumo | cronograma postergado automaticamente |
| Atraso > 5 dias úteis em VPN/credencial | taxa de ociosidade de 4h/dia (R$ 256/h) |
| Atraso > 20 dias corridos | suspensão automática dos serviços |

**Data de emissão deste questionário: 31/08/2026.** O prazo de 11/09/2026 para
os blocos A, B, D, F e G segue o marco da Onda 0. O bloco E (GCP) tem prazo
**04/09/2026** por ser pré-requisito de todo o restante. O bloco C tem prazo
**25/09/2026**, exceto C4 (CCEE), cujo prazo é **18/09/2026**.
