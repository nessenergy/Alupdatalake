---
titulo: Relatório de situação 08/09/2026 — AlupData Fase 1
documento: Relatório de situação
referencia: REL-2026-09-08 · AlupData Fase 1
emitido_em: 08 de setembro de 2026
emitente: ness. Processos e Tecnologia Ltda.
destinatario: Alup
contrato: CPS-01025/2026 — AlupData Fase 1: DataLake
marco: Onda 0 · 15,52% · R$ 23.040,00
responsavel: Ricardo Esper
classificacao: Confidencial — uso restrito das partes
local_data: 08 de setembro de 2026
---

# Situação dos insumos pendentes e do cronograma da Onda 0

## 1. Objeto

Registro da situação em 08/09/2026, primeiro dia útil da semana S2
(07/09 – 11/09), abrangendo: o estado do insumo A3, a contagem de prazos da
cláusula 3ª, os insumos com vencimento em 11/09, o escopo da S2 e a posição
atual da entrega.

## 2. Insumo A3 — ambiente GCP

O ambiente GCP `dev` tinha prazo útil em **04/09/2026** e não foi
disponibilizado. O atraso foi registrado na própria data, em
[relatório de 04/09](2026-09-04-a3-nao-entregue.md), e a situação permanece
inalterada.

Como 05 e 06 recaíram sobre o fim de semana e 07 foi feriado nacional, **08/09 é
o primeiro dia útil de atraso**.

A pendência **G1** — resposta do Google à revisão arquitetural enviada em
04/09 — permanece **sem prazo acordado**
([issue #77](https://github.com/nessenergy/Alupdatalake/issues/77)). Com a
decisão da Alup de condicionar A3 a G1, a dependência é sequencial:

    G1 (Google responde) → A3 (ambiente GCP) → 1º apply → Onda 0 homologada

**Solicitação:** definição de uma data para G1. Sem ela, o cronograma não
admite previsão.

## 3. Contagem de prazos — cláusula 3ª

| Marco | Data | Efeito |
|---|---|---|
| 1º dia útil de atraso de A3 | **08/09/2026** | contagem em curso |
| 5º dia útil | **14/09/2026** | postergação dos prazos dependentes de A3 |
| 20 dias corridos | **24/09/2026** | hipótese de suspensão dos serviços |

Conforme registrado em 04/09, o condicionamento de A3 a G1 não interrompe a
contagem: o contrato considera o atraso do insumo, não o seu motivo.

## 4. Insumos com vencimento em 11/09/2026

Prazo restante: **três dias úteis**.

| # | Insumo | Efeito da não disponibilização | Issue |
|---|---|---|---|
| A4 | Questionário de Gaps respondido (47 perguntas) | os 8 domínios analíticos não se definem; a camada Gold fica sem alvo | [#8](https://github.com/nessenergy/Alupdatalake/issues/8) |
| A9 | Token do Hubspot | conector concluído permanece sem execução; nenhum registro de CRM é ingerido | [#11](https://github.com/nessenergy/Alupdatalake/issues/11) |
| A5 | Matriz RACI e data owners | questões de regra de negócio sem destinatário definido | [#9](https://github.com/nessenergy/Alupdatalake/issues/9) |
| A6 | Ferramenta de BI definida | Portal MVP e views Gold sem consumidor definido | [#10](https://github.com/nessenergy/Alupdatalake/issues/10) |
| — | Destinatários de alerta e `billing_account` | alertas e orçamento configurados, sem destinatário | [#87](https://github.com/nessenergy/Alupdatalake/issues/87) |

**A4 é o único insumo desta lista que não depende do ambiente GCP.** Ainda que
A3 e G1 sejam resolvidos de imediato, sem as respostas do questionário a semana
S3 fica sem escopo executável, por ausência de alvo para a camada Gold.

## 5. Escopo previsto para a S2

O plano semanal condiciona a totalidade desta semana à disponibilização de A3.

| Item previsto | Situação |
|---|---|
| `terraform apply` — datasets, bucket, secrets, IAM, Cloud Run Job, Scheduler | postergado |
| Imagem da CLI no Artifact Registry e job executado contra o BCB | postergado |
| `make deploy-views` — views Silver e Gold das 5 fontes aplicadas no ambiente | postergado |
| Hubspot executado contra a API real | depende de A9 |
| Destinatários de alerta e `billing_account` | depende da Alup |

Sem o ambiente, esta frente não produz entregável verificável. O tempo tem sido
redirecionado para trabalho independente de insumo, mas essa reserva é limitada
e encontra-se substancialmente consumida.

## 6. Posição da entrega

### 6.1 Concluído

| Entrega | Onda |
|---|---|
| Terraform — módulos base | 0 |
| CI/CD em GitHub Actions | 0 |
| Documentação da arquitetura Medallion | 0 |
| Conector BCB/PTAX, de referência | 0 |
| Decisão de região do ambiente (ADR 009) | 0 |
| Conectores ONS, ANEEL e IBGE | 1 |

### 6.2 Antecipado em relação à janela contratual

| Onda | Janela contratual | Situação |
|---|---|---|
| 1 — Mercado base | 14/09 – 16/10 | **4 de 5 fontes completas**, com os 7 componentes cada: BCB/PTAX, IBGE/IPCA, ANEEL/SIGA (25.263 registros verificados, 0 inválidos) e ONS/carga. Resta a CCEE, bloqueada na origem |
| 2 — APIs credenciadas | 19/10 – 13/11 | **Hubspot completo**, os 7 componentes, escritos antes do token |
| 3 — Sistemas internos | 16/11 – 18/12 | **Caminho de acesso a bancos concluído** — Oracle, MySQL e SQL Server |
| 4 — Planilhas e handoff | 21/12 – 08/01 | **Motor de ingestão de planilhas** concluído; templates dependem de A4 |

### 6.3 Ressalva

**Nenhuma entrega foi validada contra ambiente GCP real**, uma vez que ele não
existe. Nenhum dos itens acima foi conferido pela Alup. Entrega técnica não
constitui homologação: a Onda 0 não deve ser declarada homologada antes do
primeiro `apply` e da primeira carga real.

## 7. Registro sobre a cláusula 8ª

A `main` do repositório não admite revisão obrigatória, por indisponibilidade
do recurso no plano GitHub da organização. O CI executa SAST e SCA em toda
alteração — Ruff, pytest, Bandit, pip-audit, Gitleaks e Terraform, sete
verificações —, sem impedir envio direto.

A decisão está formalizada em ADR, com os gatilhos de reabertura. Decorre dela
que **o dossiê de homologação da Onda 0 não afirmará a existência de barreira
preventiva de SAST e SCA**, descrevendo o arranjo efetivo: varredura
sistemática em toda alteração, acrescida do aceite de risco registrado.

## 8. Solicitações

| # | Solicitação | Prazo | Issue |
|---|---|---|---|
| 1 | Definição de data para G1 | imediato | [#77](https://github.com/nessenergy/Alupdatalake/issues/77) |
| 2 | A4 — Questionário de Gaps respondido | 11/09 | [#8](https://github.com/nessenergy/Alupdatalake/issues/8) |
| 3 | A9, A5 e A6, conforme seção 4 | 11/09 | [#11](https://github.com/nessenergy/Alupdatalake/issues/11), [#9](https://github.com/nessenergy/Alupdatalake/issues/9), [#10](https://github.com/nessenergy/Alupdatalake/issues/10) |
| 4 | A3 — provisionamento do ambiente GCP | condicionado a G1 | [#55](https://github.com/nessenergy/Alupdatalake/issues/55) |
| 5 | Decisão sobre a CCEE — 32h da Onda 1 sem execução | 18/09 | [#52](https://github.com/nessenergy/Alupdatalake/issues/52) |

Permanecemos à disposição para esclarecimentos.

---

*Situação corrente em [`../status.md`](../status.md). Questões abertas
acompanhadas na [issue #57](https://github.com/nessenergy/Alupdatalake/issues/57).*
