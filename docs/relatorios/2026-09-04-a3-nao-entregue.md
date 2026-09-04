# Situação do ambiente GCP e do cronograma da Onda 0

**Emitido em 04/09/2026** · Contrato CPS-01025/2026 · Marco em jogo: Onda 0 ·
15,52% · R$ 23.040,00

Prezados,

Este relatório registra a situação do insumo **A3 — provisionamento do ambiente
GCP `dev`** na data de hoje, seu efeito sobre o cronograma, e o que a ness.
segue entregando enquanto ele não chega.

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

## 4. O que seguimos entregando

O trabalho que não depende do ambiente continua sem interrupção:

| Frente | Situação |
|---|---|
| Framework, CLI, 5 conectores, motor de planilha, Portal MVP | entregues · 246 testes, 92% de cobertura, CI verde |
| Terraform completo — datasets, bucket, secrets, job, scheduler, IAM, alertas | escrito e validado; aguarda apenas o `apply` |
| **Região do ambiente definida** — `southamerica-east1` | [ADR 009](../arquitetura/decisoes/009-regiao-do-ambiente.md), emitida hoje |
| **Rótulo de custo por fonte** no job do BigQuery | implementado hoje; precisa existir antes do 1º apply, pois custo já gasto não se rateia depois |
| Revisão arquitetural para o Google | enviada em 04/09 |
| Instrumental de acompanhamento semanal — 5 campos e runbook | versionado; falta criar os campos no quadro |

Vale a transparência: **nenhuma dessas frentes fecha onda.** Fechar onda exige
dado real em BigQuery real. O que elas garantem é que, no dia em que A3 chegar,
a tarefa seja executar — e não começar.

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
