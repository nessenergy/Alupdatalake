# Situação do ambiente GCP e do cronograma da Onda 0

**Emitido em 04/09/2026** · Contrato CPS-01025/2026 · Marco em jogo: Onda 0 ·
15,52% · R$ 23.040,00

Prezados,

Este relatório registra a situação do insumo **A3 — provisionamento do ambiente
GCP `dev`** na data de hoje e seu efeito sobre o cronograma. Registra também,
com o mesmo destaque, o estado da entrega: quatro das cinco ondas já têm
trabalho concluído, e é importante que as duas leituras cheguem juntas.

Emitimos o registro no dia em que a situação se configura, e não mais adiante,
porque é assim que a cláusula 3ª funciona: ela sustenta a postergação de prazos
quando as datas estão anotadas quando ocorrem. Não se trata de formalizar uma
cobrança — trata-se de manter o histórico do projeto íntegro para os dois lados,
inclusive para nós, que precisamos justificar como as horas foram alocadas.

---

## 1. Onde estamos

O insumo **A3** tinha prazo útil em **04/09/2026** e não foi disponibilizado até
esta data. Ele compreende o projeto GCP criado, as APIs habilitadas, o IAM
concedido, o Workload Identity Federation configurado, o Artifact Registry e o
bucket de state do Terraform.

O pedido está registrado nas issues
[#1](https://github.com/nessenergy/Alupdatalake/issues/1) e
[#55](https://github.com/nessenergy/Alupdatalake/issues/55), com cobrança por
escrito em 31/08.

## 2. A informação nova, e por que ela muda o quadro

A Alup nos informou que optou por **condicionar A3 à resposta do Google** à
revisão arquitetural que enviamos hoje (pendência **G1**,
[issue #77](https://github.com/nessenergy/Alupdatalake/issues/77)).

Compreendemos a escolha e a consideramos tecnicamente defensável: é melhor
receber a crítica antes de instanciar o ambiente do que depois. Nosso próprio
material foi escrito com esse argumento.

O que precisamos registrar é o efeito da escolha sobre a forma da dependência.
O que eram duas esperas paralelas passou a ser uma cadeia em série:

    G1 (Google responde) → A3 (ambiente GCP) → 1º apply → Onda 0 homologada

E aqui está o ponto que pedimos atenção: **G1 não tem prazo acordado**. A3 ao
menos tinha data. Enquanto G1 não tiver, o cronograma não fica com uma previsão
ruim — fica sem previsão, que é uma situação diferente e mais difícil de
planejar.

## 3. Efeito sobre o cronograma

- Os prazos que dependem de A3 ficam **postergados pelo tempo do atraso**, e a
  ness. não responde pelos marcos cujo insumo não pôde ser disponibilizado.
- **S2** (07–11/09, primeiro deploy real) e **S3** (14–18/09, fechamento da
  Onda 0) escorregam integralmente enquanto o ambiente não existir.
- A **Onda 0 não pode ser homologada** sem carga real. Entrega técnica não é
  homologação: é o primeiro `apply` que revela IAM insuficiente, cota de API,
  permissão de bucket e formato recusado pelo BigQuery — e é justamente por
  isso que insistimos nele.
- Registramos, sem que isso implique qualquer objeção à decisão de aguardar,
  que **condicionar A3 a G1 não interrompe a contagem** prevista na cláusula
  3ª, uma vez que o contrato considera o atraso do insumo e não o seu motivo.

## 4. O outro lado do quadro: a entrega está adiantada

Este relatório trata de um atraso, e por isso pedimos atenção a um dado que a
leitura isolada esconde: **no quinto dia da primeira onda, quatro das cinco já
têm entrega**.

| Onda | Janela contratual | O que já existe |
|---|---|---|
| **1** — Mercado base | 14/09 – 16/10 | **4 de 5 fontes completas**, com os 7 componentes cada: BCB/PTAX, IBGE/IPCA, ANEEL/SIGA (25.263 registros verificados) e ONS/carga. Só a CCEE falta, bloqueada na origem |
| **2** — APIs credenciadas | 19/10 – 13/11 | **Hubspot completo**, os 7 componentes, escritos contra a documentação pública antes do token |
| **3** — Sistemas internos | 16/11 – 18/12 | **Caminho de acesso a bancos pronto** — Oracle, MySQL e SQL Server, com credencial em cofre e leitura paginada |
| **4** — Planilhas e handoff | 21/12 – 08/01 | **Motor de ingestão de planilhas** pronto; faltam os templates, que dependem do Questionário de Gaps |

A fonte do adiantamento é simples: sempre que uma frente não dependia de insumo
da Alup, ela foi puxada para frente. O motor de planilha, cuja janela abre em
21/12, está pronto desde 26/08 — três meses e meio de antecedência.

O efeito prático disso aparece justamente no item de maior risco financeiro do
contrato. Quando a VPN e as credenciais da Onda 3 chegarem, a tarefa será
apontar a conexão e escrever as consultas, **não construir a capacidade de ler
banco**. O que se perde esperando deixou de ser desenvolvimento pendente.

### Outras frentes concluídas fora do escopo faturado

| Frente | Situação |
|---|---|
| Framework, CLI e reprocessamento de dado bruto | entregues · **279 testes**, 92% de cobertura, CI verde |
| Terraform completo — datasets, bucket, secrets, job, agendamento, IAM, alertas | escrito e validado; aguarda apenas o `apply` |
| Permissões restringidas por recurso, credencial removida de log e de erro | cláusula 8ª · conta de serviço deixou de ter acesso amplo ao projeto |
| **Região do ambiente definida** — `southamerica-east1` | [ADR 009](../arquitetura/decisoes/009-regiao-do-ambiente.md), emitida hoje |
| **Atribuição de custo por fonte** no BigQuery | precisa existir **antes** do 1º apply: custo já gasto não se rateia depois |
| Portal MVP com painéis de saúde e de custo | roda com provedor simulado; aguarda o ambiente |
| Instrumental de acompanhamento semanal | cinco campos criados no quadro hoje |

### A ressalva que pedimos que fique registrada

**Nenhuma dessas frentes fecha onda.** Fechar onda exige dado real em BigQuery
real, e isso depende do ambiente.

As duas coisas são verdadeiras ao mesmo tempo e não se anulam: o projeto está
**adiantado em entrega e parado em homologação**. Relatar só a primeira metade
seria vender progresso que não fecha marco; relatar só a segunda esconderia
trabalho já feito e pago. É o segundo lado que define quando o marco pode ser
medido.

## 5. Como podemos ajudar a destravar

| # | Insumo | Com quem | Situação |
|---|---|---|---|
| **G1** | Uma data para a resposta do Google | Alup / Google | sem prazo acordado — é o item que hoje precede todo o resto |
| **A3** | Ambiente GCP `dev` provisionado | Alup | vencido em 04/09, condicionado a G1 |
| **A1** | WIF no lado do GitHub (`GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`) | Alup | sem ele o deploy não autentica, mesmo com A3 pronto |

**Nosso pedido é modesto: uma data para G1.** Não a resposta completa — apenas
a data. Com ela, a postergação passa a ser calculável e voltamos a planejar as
semanas seguintes com previsibilidade.

Permanecemos à disposição para participar da conversa com o Google, preparar
material adicional ou antecipar qualquer frente que ajude a encurtar o caminho.

Atenciosamente,

**Ricardo Esper**
ness. Processos e Tecnologia
