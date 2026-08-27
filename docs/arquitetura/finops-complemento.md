# FinOps — complemento ao plano do portal de custo

**Status**: complemento · **Data**: 2026-08-27 · **Contribuição comercial da ness., não faturada**

O plano de FinOps é o [`portal-finops.md`](portal-finops.md) (issue #58,
PR #56), e as decisões de implementação estão na
[ADR 007](decisoes/007-portal-de-custo.md). Este arquivo **não repete** aquele
plano — ele registra dois detalhes de implementação que só aparecem quando se
vai escrever o código, para que não sejam descobertos no meio da execução.

Enquadramento, herdado do plano e da decisão de 27/08: observabilidade de custo
é **sustentação (cláusula 10ª)**, pelo mesmo argumento da ADR 006 — mostra o
comportamento do pipeline, não dado de cliente. É entrega comercial da ness.,
**fora do escopo faturado**; não entra em medição nem consome a franquia de
20h/mês. Só a camada F3 (gestão de FinOps para a diretoria) é aditivo, pela
cláusula 5ª.

---

## 1. O billing export pode ser a primeira exceção legítima à regra 5

O plano (§6) já diz que habilitar o billing export exige papel na conta de
faturamento, separado de A3. Falta dizer **onde o interruptor mora**: até onde
apuramos, ligar o export para o BigQuery é configuração da *conta de
faturamento*, feita no console, **sem recurso Terraform equivalente**.

Se confirmado na hora de fazer a F2, isso tem duas consequências que precisam
estar ditas antes, não depois:

- O dataset de destino e o IAM ficam no Terraform; **o interruptor do export,
  não** — e essa é a primeira exceção legítima à regra 5 do projeto ("recurso
  GCP que não está em `infra/` não existe"). Exceção documentada não é furo de
  processo; exceção descoberta em produção é.
- Vira passo manual de runbook, com dono nomeado. O `google_billing_budget` que
  já está escrito no módulo `monitoramento` depende do mesmo `billing_account`,
  então os dois destravam juntos.

**A verificar antes de fechar a F2**: se existe caminho Terraform para o export
(recurso ou módulo de terceiro). Se existir, esta ressalva cai.

## 2. As views de custo precisam de uma exceção no teste de camadas

`tests/unit/test_sql.py::test_view_referencia_a_camada_anterior` exige que toda
view Gold leia da Silver, e hoje abre **uma** exceção: a view de monitoramento
que lê `bronze._execucoes`.

`gold.custo_consultas` (F1) não lê nem Silver nem Bronze — lê
`INFORMATION_SCHEMA.JOBS` e, para armazenamento, `TABLE_STORAGE`. Ou seja, a
F1 precisa **estender** aquela exceção, e da mesma forma estreita: view de custo
não pode juntar `INFORMATION_SCHEMA` com dado de negócio, pela mesma regra que
hoje proíbe misturar log de execução com dado de negócio. Sem estender o teste,
a F1 chega quebrando o CI por um caso que é legítimo; estendê-lo às cegas abre
brecha para a mistura que a regra existe para impedir. A exceção tem de nomear
as duas fontes de sistema (`_execucoes` e `INFORMATION_SCHEMA`) e continuar
proibindo o resto.

---

## O que este complemento **não** acrescenta

Para não duvidar depois: rótulo por fonte, a limitação de compute não-atribuível,
o custo fixo por execução dominar a conta hoje, o rateio por fonte via rótulo de
job, e as três visões (operacional/orçamento/diretoria) **já estão no plano** —
`portal-finops.md`, §§4, 5 e 9. Este arquivo só cobre os dois pontos acima.
