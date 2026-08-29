# Questionário de Gaps — AlupData Fase 1

**Contrato** CPS-01025/2026 · **Onda 0** · dependência **A4** (cláusula 3ª)
**Emitido por** ness. Processos e Tecnologia · **Para** Grupo Alupar
**Data de emissão** 29/08/2026 · **Prazo de resposta** 11/09/2026

---

## Como usar

47 perguntas em 7 blocos. Cada bloco tem um destinatário provável — a coluna
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
| A1 | **[BLOQUEIA]** Quais são as 8 perguntas de negócio que este DataLake precisa responder no primeiro ano? Enumere em linguagem de negócio, não de sistema. | Diretoria / Comercial | |
| A2 | **[BLOQUEIA]** Dessas 8, quais 3 dão retorno mais rápido se entregues primeiro? | Diretoria | |
| A3 | Hoje, essas perguntas são respondidas como? (planilha, relatório manual, sistema, ninguém responde) | Comercial / Controladoria | |
| A4 | Quem consome cada resposta e com que frequência (diária, semanal, mensal, sob demanda)? | Cada área | |
| A5 | Existe algum indicador/KPI já formalizado e com fórmula acordada entre as 6 coligadas? Se sim, envie a definição. | Controladoria | |
| A6 | Há métrica que hoje é calculada de formas diferentes por coligada? Qual, e qual versão vale? | Controladoria | |
| A7 | Qual granularidade mínima é aceitável para decisão: usina, coligada, submercado, grupo? | Comercial | |

---

## Bloco B — Donos de dados e governança (6)

Dependência **A5** (matriz RACI). Sem dono, dúvida de regra de negócio não tem
para quem ir, e a ness. para de trabalhar esperando resposta.

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| B1 | **[BLOQUEIA]** Quem é o **data owner** de cada domínio definido no bloco A? Nome, área e e-mail. | Diretoria | |
| B2 | **[BLOQUEIA]** Quem é o ponto focal técnico da Alup para desbloqueio de acesso (VPN, credencial, firewall)? Nome e substituto. | TI | |
| B3 | Qual o SLA interno da Alup para responder uma dúvida de regra de negócio? | Diretoria | |
| B4 | Quem aprova formalmente a homologação de cada onda e assina a medição? | Diretoria / Compras | |
| B5 | Existe comitê ou fórum recorrente onde o projeto será acompanhado? Data e participantes. | PMO | |
| B6 | Há política de governança de dados já escrita na Alup (classificação, qualidade, retenção)? Envie. | Compliance | |

---

## Bloco C — Fontes e sistemas internos (10)

Ondas 2 e 3. **A7** é o maior risco financeiro do contrato: atraso > 5 dias
úteis em VPN/credencial dispara ociosidade de 4h/dia (R$ 256/h, cláusula 3ª).

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| C1 | **[BLOQUEIA]** Os pedidos internos de token (Onda 2) e VPN/credencial read-only (Onda 3) já foram **abertos**? Envie os números de chamado. | TI | |
| C2 | **[BLOQUEIA]** Qual o prazo real do processo interno de liberação de acesso a banco de produção, do pedido à credencial na mão? | TI / Segurança | |
| C3 | **[BLOQUEIA]** A Alup consegue fornecer a **documentação técnica de BBCE e TempoOK** (contratos de API, manuais do fornecedor)? Ela vale tanto quanto o token e pode vir antes. | Comercial | |
| C4 | **[BLOQUEIA]** CCEE InfoMercado responde 403 a acesso automatizado. Qual caminho a Alup escolhe: (a) liberar IP junto à CCEE, (b) fornecer credencial de agente, (c) remanejar as 32h para outro escopo? | Comercial | |
| C5 | Oracle FMB: versão, host, porta, nome do schema, e existe réplica de leitura? | TI | |
| C6 | Portal Alup: quais bases exatamente (MySQL, NoSQL, Storage), e qual o volume aproximado de cada uma? | TI | |
| C7 | RM/TOTVS: a integração será por API, view de banco ou exportação? Existe ambiente de homologação? | TI | |
| C8 | MySQL RDS Comercialização: está em qual nuvem/região, e há peering ou precisa de VPN? | TI | |
| C9 | Para cada sistema interno: qual a janela em que a extração pode rodar sem impactar a operação? | TI | |
| C10 | Há alguma fonte relevante que **não** está na lista do contrato e deveria estar? | Todas as áreas | |

---

## Bloco D — Regras de negócio e camada Gold (7)

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| D1 | Como se identifica uma usina de forma única entre os sistemas? O CodCEG da ANEEL serve como chave, ou há código interno? | Engenharia | |
| D2 | Qual o código de agente CCEE de cada uma das 6 coligadas? | Comercial | |
| D3 | Uma usina pode mudar de coligada ao longo do tempo? Se sim, o histórico deve seguir a usina ou a coligada? | Controladoria | |
| D4 | Qual o calendário de apuração que vale: mês civil, mês CCEE, ou ambos? | Controladoria | |
| D5 | Como tratar retificação de dado já publicado (ex.: CCEE recontabiliza mês fechado) — sobrescrever ou versionar? | Controladoria | |
| D6 | Quais conversões de unidade e moeda são obrigatórias (MWh/MWm, R$/US$) e qual a fonte oficial da taxa? | Controladoria | |
| D7 | Há regra de arredondamento ou truncamento que a Alup exige em valor financeiro? | Controladoria | |

---

## Bloco E — Ambiente GCP e acessos (7)

Dependência **A3**, prazo **04/09**. É a mais urgente: nada sobe sem ela, e a
Onda 0 não homologa. Todo o cronograma pendura nesta linha.

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| E1 | **[BLOQUEIA]** Qual a **data e o responsável** pela criação do projeto GCP `dev`? Precisamos de data com nome, não de estimativa. | TI | |
| E2 | **[BLOQUEIA]** Qual a `billing_account` a ser vinculada, e qual o teto mensal de custo aceitável para o alerta de orçamento? | Controladoria / TI | |
| E3 | **[BLOQUEIA]** Quem recebe os alertas de falha de ingestão? Envie e-mails ou canal (a infraestrutura de alerta existe e está sem destinatário). | TI | |
| E4 | A Alup provisiona também o projeto de **produção** agora, ou só `dev` nesta fase? | TI | |
| E5 | Existe organização/pasta GCP e política de nomenclatura corporativa que devemos seguir? | TI | |
| E6 | Quem administra o Workload Identity Federation para o deploy via GitHub Actions? | TI | |
| E7 | Há restrição de região? Assumimos `southamerica-east1` (São Paulo) — confirma? | TI | |

---

## Bloco F — Segurança, LGPD e retenção (5)

Cláusula 8ª. Perguntas cuja resposta muda o desenho, não só a operação.

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| F1 | Alguma das fontes contém **dado pessoal** (CPF, nome, contato — o Hubspot muito provavelmente sim)? Quais campos? | Compliance / DPO | |
| F2 | Se sim, qual a base legal e o tratamento exigido: mascarar, pseudonimizar, ou restringir acesso por IAM? | DPO | |
| F3 | Qual a política de retenção por camada (Bronze bruto, Silver, Gold)? Há obrigação regulatória de guardar por N anos? | Compliance | |
| F4 | Há classificação de informação corporativa (público/interno/confidencial) que devemos aplicar aos datasets? | Segurança | |
| F5 | O relatório de SAST/SCA do CI precisa ser enviado a alguma área da Alup periodicamente? Para quem e com que frequência? | Segurança | |

---

## Bloco G — Consumo, BI e planilhas (5)

Dependências **A6** (BI) e insumo do motor S2 Data Intake da Onda 4.

| # | Pergunta | Quem | Resposta |
|---|---|---|---|
| G1 | **[BLOQUEIA]** Qual a ferramenta de BI definitiva: Power BI, Looker Studio, Tableau, outra? A escolha muda o formato de entrega das views Gold. | TI / Diretoria | |
| G2 | Já existem licenças contratadas dessa ferramenta, e quantos usuários? | TI | |
| G3 | Quais planilhas hoje alimentam decisão e deveriam entrar pelo S2 Data Intake? Envie exemplos reais dos arquivos. | Cada área | |
| G4 | Quem mantém cada planilha, e com que periodicidade ela é atualizada? | Cada área | |
| G5 | Qual profundidade de histórico é necessária na primeira carga (ex.: ONS desde 2018 ou só 2026)? Isso tem impacto direto em custo de BigQuery. | Controladoria | |

---

## Efeito contratual de não responder

Registrado aqui porque a cláusula 3ª exige que a data do pedido conste do dia em
que o atraso começa, não do dia em que vira problema.

| Situação | Efeito |
|---|---|
| Atraso > 5 dias úteis em qualquer insumo | cronograma postergado automaticamente |
| Atraso > 5 dias úteis em VPN/credencial | taxa de ociosidade de 4h/dia (R$ 256/h) |
| Atraso > 20 dias corridos | suspensão automática dos serviços |

**Data de emissão deste questionário: 29/08/2026.** O prazo de 11/09/2026 para
os blocos A, B, D, F e G segue o marco da Onda 0. O bloco E (GCP) tem prazo
**04/09/2026** por ser pré-requisito de todo o restante. O bloco C tem prazo
**25/09/2026**, exceto C4 (CCEE), cujo prazo é **18/09/2026**.
