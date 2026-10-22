# Onda 1: CPTEC, IPDO e ACOMPH — plano de execução

**Spec:** [`../specs/2026-10-22-onda1-ipdo-acomph-cptec-design.md`](../specs/2026-10-22-onda1-ipdo-acomph-cptec-design.md)

**Meta:** entregar o CPTEC com os 7 componentes e deixar IPDO e ACOMPH prontos para decidir ou destravar.

## Global Constraints

- As 6 regras do `AGENTS.md`. Credencial só no Secret Manager; recurso GCP só em `infra/`; sem atribuição de ferramenta de IA.
- TDD: teste antes do código. Código em inglês; comentário, doc e commit em português.

## Tarefas

| # | Tarefa | Estado |
|---|---|---|
| 1 | Reprovar as três origens em 22/10 (CPTEC, SINtegre, IPDO) | feito |
| 2 | Conector `cptec_previsao`: teste com a fixture real, depois o código (retrato das 27 capitais) | feito, 10 testes |
| 3 | Bronze, Silver (com `rowConditions`) e Gold `previsao_tempo_capitais` | feito |
| 4 | Agendamento diário (`infra/modules/scheduler`), alerta de frescor (`monitoramento`, `silencio.js`), custo, catálogo, `conferir_cargas` | feito |
| 5 | Dicionário com linhagem e adendo nas ADRs 028 e 029 | feito |
| 6 | PR, CI e merge | a fazer |
| 7 | Deploy em dev e primeira carga: `Executar ingestão` com `cptec_previsao`, depois `Conferir cargas` (esperado: 162 linhas) | a fazer, depois do 6 |
| 8 | Hml e atualizar `status.md`, `plano-execucao.md` e o painel (marco do CPTEC) | a fazer, depois do 7 |
| 9 | IPDO: levar o pedido de aceite da ADR 027, seção 5, à Alupar | decisão do Ricardo |
| 10 | ACOMPH: pedir à Alupar o produto do login e ao ONS a documentação da API do SINtegre; ao receber, escrever spec do conector | depende de terceiros |
