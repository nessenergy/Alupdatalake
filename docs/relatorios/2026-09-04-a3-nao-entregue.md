# Registro de atraso — A3 (ambiente GCP) não entregue no prazo

**Emitido em 04/09/2026** · Contrato CPS-01025/2026 · Marco em jogo: Onda 0 ·
15,52% · R$ 23.040,00

Este relatório existe por uma razão só: **registrar, no dia em que o atraso
começa, que o insumo A3 não foi disponibilizado.** A cláusula 3ª só sustenta
postergação se a data do pedido e a data do atraso estiverem registradas quando
ocorrem — não quando viram problema.

---

## 1. O fato

**A3 — provisionamento do ambiente GCP `dev`** tinha prazo útil em **04/09/2026**
e **não foi entregue até esta data**.

A3 compreende: projeto GCP criado, as APIs habilitadas, IAM concedido, Workload
Identity Federation configurado, Artifact Registry criado e bucket de state do
Terraform disponível.

Pedido e acompanhamento registrados nas issues
[#1](https://github.com/nessenergy/Alupdatalake/issues/1) e
[#55](https://github.com/nessenergy/Alupdatalake/issues/55); cobrança por
escrito feita em 31/08, primeiro dia da S1.

## 2. A informação nova de hoje

A Alup informou que **condicionou A3 à resposta do Google** à revisão
arquitetural que a ness. enviou em 04/09 (pendência **G1**).

Isso transforma o que eram duas esperas paralelas em uma **cadeia em série**:

    G1 (Google responde) → A3 (ambiente GCP) → 1º apply → Onda 0 homologada

**G1 não tem prazo acordado.** Enquanto não tiver, o cronograma do contrato não
tem previsão de retomada — o que é diferente de ter uma previsão ruim.

## 3. Efeito contratual

- Os prazos que dependem de A3 ficam **postergados pelo tempo do atraso**. A
  ness. **não responde pelos marcos cujo insumo não foi disponibilizado**.
- **S2** (07–11/09, primeiro deploy real) e **S3** (14–18/09, fechar a Onda 0)
  escorregam integralmente enquanto A3 não chegar.
- A **Onda 0 não pode ser homologada** sem carga real: entrega técnica não é
  homologação, e é o primeiro `apply` que revela IAM insuficiente, cota de API,
  permissão de bucket e formato recusado pelo BigQuery.
- **Condicionar A3 a G1 não interrompe a contagem.** O contrato conta o atraso
  do insumo, não o motivo. A decisão de aguardar o Google é legítima e pode ser
  tecnicamente acertada — o registro aqui não a contesta, apenas preserva o
  efeito contratual, que continua correndo.

## 4. O que a ness. segue entregando

O trabalho que não depende do ambiente continua, sem interrupção:

| Frente | Situação |
|---|---|
| Framework, CLI, 5 conectores, motor de planilha, Portal MVP | entregues; 241 testes, 92% de cobertura, CI verde |
| Terraform completo (datasets, bucket, secrets, job, scheduler, IAM, alertas) | escrito e validado; aguarda apenas o `apply` |
| **Região do ambiente decidida** — `southamerica-east1` | [ADR 009](../arquitetura/decisoes/009-regiao-do-ambiente.md), emitida hoje |
| Revisão arquitetural para o Google | enviada em 04/09 |
| Instrumental de acompanhamento semanal (5 campos + runbook) | versionado; falta criar os campos no quadro |
| Fila de execução com dono e comando | [`proximos-passos.md`](../proximos-passos.md) |

**Nenhuma dessas frentes fecha onda.** Fechar onda exige dado real em BigQuery
real. O que elas fazem é garantir que, no dia em que A3 chegar, a tarefa seja
executar — não começar.

## 5. O que destrava

| # | Insumo | Responsável | Situação |
|---|---|---|---|
| **G1** | Data para a resposta do Google à revisão arquitetural | Alup / Google | **sem prazo acordado** — é o item que hoje bloqueia todo o resto |
| **A3** | Ambiente GCP `dev` provisionado | Alup | vencido em 04/09; condicionado a G1 |
| **A1** | WIF no lado do GitHub (`GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`) | Alup | sem ele o deploy não autentica, mesmo com A3 pronto |

**O pedido concreto**: uma **data** para G1. Com data, o cronograma volta a ter
previsão e a postergação é calculável. Sem data, a retomada do contrato depende
de um terceiro sem compromisso de prazo.

---

*Registro emitido pela ness. Processos e Tecnologia · Ricardo Esper*
