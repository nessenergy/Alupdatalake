# Módulo Composer

**Vazio de propósito até a Onda 3** (ADR 004).

Cloud Composer cobra por ambiente ligado 24×7, e o custo de infraestrutura é da
contratante (cláusula 5ª). Enquanto a orquestração for "rodar N extrações por
dia, sem dependência entre elas", Cloud Run Job + Cloud Scheduler resolve por
uma fração do custo — é o que está em [`../scheduler`](../scheduler).

Este módulo passa a existir quando houver dependência real entre pipelines.
