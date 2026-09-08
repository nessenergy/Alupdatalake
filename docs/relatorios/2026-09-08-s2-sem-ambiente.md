# A semana do primeiro deploy sem o ambiente, e uma correção no nosso quadro

**Emitido em 08/09/2026** · Contrato CPS-01025/2026 · Marco em jogo: Onda 0 ·
15,52% · R$ 23.040,00

Prezados,

Este relatório cobre o primeiro dia útil da semana **S2 (07/09 – 11/09)**, que o
plano reservava para o primeiro deploy real, e registra três coisas: o estado do
insumo **A3**, os prazos que vencem em 11/09 e uma **correção que fizemos no
nosso próprio quadro de acompanhamento**, que vinha superestimando o avanço do
projeto.

O terceiro ponto é o que mais nos importa comunicar hoje. A informação errada
estava a nosso favor, foi encontrada por nós e está corrigida — mas ela chegou a
ficar visível, e vocês precisam saber disso antes de qualquer número subir para
a diretoria.

---

## 1. O insumo A3 segue pendente

O ambiente GCP `dev` tinha prazo útil em **04/09/2026** e não foi
disponibilizado até hoje. O registro do atraso foi emitido na própria data, em
[relatório de 04/09](2026-09-04-a3-nao-entregue.md), e a situação não mudou
desde então.

Como 05 e 06 caíram no fim de semana e 07 foi feriado nacional, **hoje é o
primeiro dia útil de atraso**. Não houve, portanto, perda de tempo útil entre um
relatório e outro — e é justamente por isso que este é um bom momento para
tratar do assunto sem urgência.

A pendência **G1**, resposta do Google à revisão arquitetural que enviamos em
04/09, permanece **sem prazo acordado**
([issue #77](https://github.com/nessenergy/Alupdatalake/issues/77)). Como a Alup
optou por condicionar A3 a G1, a cadeia continua em série:

    G1 (Google responde) → A3 (ambiente GCP) → 1º apply → Onda 0 homologada

Seguimos considerando a escolha defensável — receber a crítica antes de
instanciar o ambiente é melhor que depois. O que pedimos é apenas que G1 ganhe
uma data, qualquer que seja. Uma previsão distante permite planejar; a ausência
de previsão, não.

## 2. O que a S2 previa, e o que acontece sem o ambiente

O plano semanal é explícito quanto a esta semana: *"Esta semana só existe se A3
chegou."* O conteúdo previsto era todo dependente do ambiente:

| Item previsto para a S2 | Situação |
|---|---|
| `terraform apply` real — datasets, bucket, secrets, IAM, Cloud Run Job, Scheduler | escorrega |
| Imagem da CLI no Artifact Registry e job executado contra o BCB | escorrega |
| `make deploy-views` — views Silver e Gold das 5 fontes existindo de verdade | escorrega |
| Hubspot rodado contra a API real | depende de A9 |
| Destinatários de alerta e `billing_account` preenchidos | depende da Alup |

Enquanto o ambiente não existir, esta frente não produz entregável verificável.
Temos redirecionado o tempo para trabalho que não depende de insumo — foi assim
que quatro das cinco ondas chegaram a ter entrega —, mas esse estoque de
trabalho independente é finito e já está bastante consumido.

## 3. O relógio da cláusula 3ª

Registramos as datas para que os dois lados tenham o mesmo quadro, não para
formalizar cobrança:

| Marco da cláusula 3ª | Data | Efeito |
|---|---|---|
| 1º dia útil de atraso de A3 | **08/09** (hoje) | contagem em curso |
| 5º dia útil | **14/09** | a partir daí, postergação dos prazos que dependem de A3 |
| 20 dias corridos | **24/09** | hipótese de suspensão dos serviços |

Vale repetir o que dissemos em 04/09: condicionar A3 a G1 não interrompe a
contagem, porque o contrato considera o atraso do insumo e não o seu motivo.
Isso não é uma objeção à decisão de aguardar o Google — é o registro que
protege os dois lados na medição.

## 4. Os prazos que vencem em 11/09

Faltam **três dias úteis** para cinco itens:

| # | Item | Efeito de não chegar | Issue |
|---|---|---|---|
| A4 | Questionário de Gaps respondido (47 perguntas) | os 8 domínios analíticos não se definem, e a camada Gold fica sem alvo | [#8](https://github.com/nessenergy/Alupdatalake/issues/8) |
| A9 | Token do Hubspot | conector pronto segue parado; nenhuma linha de CRM entra no lake | [#11](https://github.com/nessenergy/Alupdatalake/issues/11) |
| A5 | Matriz RACI e data owners | dúvida de regra de negócio não tem destinatário | [#9](https://github.com/nessenergy/Alupdatalake/issues/9) |
| A6 | Ferramenta de BI definida | Portal MVP e views Gold ficam sem consumidor definido | [#10](https://github.com/nessenergy/Alupdatalake/issues/10) |
| — | Destinatários de alerta e `billing_account` | alertas e orçamento existem, mas não notificam ninguém | [#87](https://github.com/nessenergy/Alupdatalake/issues/87) |

Chamamos atenção especial para **A4**. Ele é o único da lista que **não depende
do ambiente GCP**: mesmo que A3 e G1 se resolvam amanhã, sem as respostas do
questionário a semana S3 não tem conteúdo, porque não há alvo para a camada
Gold. A4 é, hoje, o insumo com melhor relação entre esforço de vocês e
destravamento do nosso lado.

## 5. Correção no quadro de acompanhamento

Em 24/08, ao popular o GitHub Projects, uma carga automática rodou duas vezes e
criou **15 itens duplicados**. Em 27/08 fizemos a limpeza fechando uma cópia de
cada par — e aqui está o erro: no GitHub Projects, **issue fechada conta
automaticamente como entrega concluída**. A limpeza produziu 15 conclusões que
não correspondiam a trabalho realizado.

O efeito era material. O quadro exibia **24 entregas quando o realizado eram
9**, e apresentava as Ondas 3 e 4 como tendo itens concluídos — incluindo
conectores de sistemas internos cujas credenciais sequer chegaram.

**Corrigido hoje.** Os 15 itens duplicados foram arquivados; o quadro passou de
58 para 43 itens e de 24 para **9 conclusões**, que são as reais. Uma décima
entrou ainda hoje, com o registro da decisão tratada na seção 7:

| Entrega concluída | Onda |
|---|---|
| Setup Terraform — módulos base | 0 |
| CI/CD em GitHub Actions | 0 |
| Documentação da arquitetura Medallion | 0 |
| Conectores ONS, ANEEL, IBGE e Câmbio BCB | 1 |
| Decisão de região do ambiente (ADR 009) | 0 |
| Campos de acompanhamento semanal do quadro | 0 |
| Registro da decisão sobre revisão obrigatória na `main` (ADR 010) | 0 |

Nenhuma issue foi excluída e o arquivamento é reversível — o histórico está
íntegro para auditoria.

Duas observações que consideramos devidas. A primeira: o erro favorecia a
ness., e foi encontrado e corrigido por nós, sem que ninguém o apontasse.
A segunda: ele demonstra por que o campo **Validado** existe no quadro. Entrega
técnica não é homologação. **Nenhum dos itens acima foi conferido pela Alup** —
todos estão marcados `Validado = Não` no quadro, e nenhum deles deve ser lido
como onda fechada.

## 6. O quadro de acompanhamento está pronto para uso

Atendendo à solicitação de acompanhamento semanal, o quadro agora expõe as
colunas de controle, que existiam mas não estavam visíveis nas visualizações:

- **Acompanhamento semanal** — tabela com Semana, Início, Término, Horas,
  Validado, Correções e Atraso;
- **Status semanal** — quadro com as três raias: concluídas, em andamento e a
  iniciar.

O campo **`Validado`** já está preenchido: todas as entregas concluídas estão
marcadas como **não validadas**, porque nenhuma foi conferida pela Alup até
aqui. Filtrar o quadro por `Validado = Não` dá, portanto, a **fila de
homologação** — é a lista do que depende de alguém da Alup para que uma onda
possa ser fechada.

O quadro passou a carregar também as **horas previstas por item**, transcritas
do plano de execução. Elas fecham **580 horas exatas**, e fecham por onda:

| Onda | Contratado | No quadro |
|---|---|---|
| 0 — Fundação | 90h | 90h |
| 1 — Mercado base | 120h | 120h |
| 2 — APIs credenciadas | 110h | 110h |
| 3 — Sistemas internos | 155h | 155h |
| 4 — Planilhas e handoff | 105h | 105h |
| **Total** | **580h** | **580h** |

Chegar a esse fechamento revelou duas lacunas, ambas corrigidas:

- **121 horas de escopo contratado não tinham item no quadro** — as views Gold
  de cada onda, o agendamento e monitoramento das fontes da Onda 1, a migração
  da orquestração para o Cloud Composer, a reserva de ajustes do framework, a
  reserva de fontes remanescentes e o primeiro deploy real. Eram 21% do
  contrato sem rastreio. Foram abertas oito issues, de #88 a #95, e agora todo
  item do plano tem correspondente no quadro.
- **O conector de câmbio do BCB estava atribuído à Onda 1**, quando o plano o
  registra como concluído na Onda 0, na condição de conector de referência.
  Corrigido — era o que deslocava 10 horas entre as duas ondas.

**`Horas` — o realizado — segue em branco, e deliberadamente.** É campo
distinto do previsto, e é ele que alimenta a medição. Preenchê-lo com
estimativa apresentaria previsão como apontamento, o que não faremos. Propomos
consolidar o realizado na próxima reunião de acompanhamento e mantê-lo semanal
a partir daí. O mesmo vale para `Semana`, que registra período de
desenvolvimento e não período planejado.

## 7. Registro sobre a cláusula 8ª

A `main` deste repositório não pode ter revisão obrigatória: o plano GitHub da
organização não oferece o recurso. O CI executa SAST e SCA em toda alteração —
Ruff, pytest, Bandit, pip-audit, Gitleaks e Terraform, sete verificações —, mas
não impede um envio direto.

Registramos formalmente a decisão em ADR, com os gatilhos que a reabrem, e
consignamos aqui o que dela decorre: **o dossiê de homologação da Onda 0 não
afirmará que existe barreira preventiva de SAST e SCA**. Descreverá o arranjo
real — varredura sistemática em toda alteração, mais o aceite de risco
registrado. Preferimos a descrição exata a uma afirmação confortável.

## 8. O outro lado do quadro

Este relatório trata de um atraso e de uma correção desfavorável a nós. Cabe,
por isso, repetir o dado que a leitura isolada esconde: **a entrega segue
adiantada em relação ao cronograma contratual**.

| Onda | Janela contratual | O que já existe |
|---|---|---|
| **1** — Mercado base | 14/09 – 16/10 | **4 de 5 fontes completas**, com os 7 componentes cada: BCB/PTAX, IBGE/IPCA, ANEEL/SIGA (25.263 registros verificados, 0 inválidos) e ONS/carga. Falta a CCEE, bloqueada na origem |
| **2** — APIs credenciadas | 19/10 – 13/11 | **Hubspot completo**, os 7 componentes, escritos antes do token |
| **3** — Sistemas internos | 16/11 – 18/12 | **Caminho de acesso a bancos pronto** — Oracle, MySQL e SQL Server |
| **4** — Planilhas e handoff | 21/12 – 08/01 | **Motor de ingestão de planilhas** pronto; templates dependem de A4 |

Com a ressalva que fazemos desde o início e que a correção da seção 5 só torna
mais importante: **nada foi validado contra um ambiente GCP real**, porque ele
ainda não existe. Onda 0 não deve ser declarada homologada antes do primeiro
`apply` e da primeira carga real.

## 9. O que pedimos

1. **Uma data para G1**, ainda que distante — [issue #77](https://github.com/nessenergy/Alupdatalake/issues/77).
2. **A4 respondido até 11/09** — é o insumo que mais destrava por menos esforço,
   e o único que não depende do ambiente.
3. **A3 provisionado** assim que a resposta do Google permitir — [issue #55](https://github.com/nessenergy/Alupdatalake/issues/55).
4. **A9, A5 e A6 até 11/09**, conforme a seção 4.
5. **Decisão sobre a CCEE até 18/09** — 32 horas da Onda 1 seguem paradas
   ([issue #52](https://github.com/nessenergy/Alupdatalake/issues/52)).

Permanecemos à disposição para tratar de qualquer ponto deste registro, e
agradecemos a atenção de sempre.

---

*Situação corrente e viva em [`../status.md`](../status.md). Questões abertas
acompanhadas na [issue #57](https://github.com/nessenergy/Alupdatalake/issues/57).*
