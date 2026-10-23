# Débitos que se resolvem sem terceiros — especificação

Data: 23/10/2026. Origem: a pergunta "há algo em débito que poderíamos resolver já?" e o levantamento feito em seguida.
Base: [plano de débitos técnicos de 05/10](../plans/2026-10-05-debitos-tecnicos.md), `docs/status.md` e as pendências do CI e CD de 22/10.

## 1. O que entra, e o que não entra

| # | Débito | Por que agora | Entra |
|---|---|---|---|
| 1 | Asserção do Hubspot reprova o Dataform em dev e hml | É o único motivo de o `Deploy GCP` terminar com falha, e o e-mail à Alupar prometeu enviar a lista de negócios | sim |
| 2 | `google-api-core` 2.35.0 está retirado (yanked) | Aviso fixo em todo `uv lock` | sim |
| 3 | T6: toda Silver na conferência ou numa exceção declarada | Fonte nova não passa sem verificação | sim |
| 4 | T5: motivo dos testes ignorados | O motivo já existe no relatório de 22/10, falta o documento | sim |
| 5 | `deploy.md` sem os gatilhos novos | A documentação ficou atrás do que foi mesclado | sim |
| — | Tabelas residuais do CPTEC no BigQuery | Apagar dado é irreversível | **não**, aguarda decisão |
| — | T7 (fechamento do plano de débitos) | Depende de T5, T6 e das decisões D | **não** |
| — | D1 a D4, papel de log em dev, hml | Dependem de pessoas | **não** |

## 2. Decisões de desenho

### 2.1 Diagnóstico do Hubspot (item 1)
- Dois itens novos na conferência de cargas, **somente leitura** (a validação do `conferir_cargas.py` já recusa tudo que não for `SELECT` ou `WITH`):
  - `hubspot_negocios_fora_da_regra`: o total de negócios e a contagem que viola cada regra da Silver (`valor < 0`; `data_fechamento` anterior à data de criação). As duas regras são exatamente as `rowConditions` de `definitions/silver/hubspot_negocios.sqlx`.
  - `hubspot_negocios_reprovados`: até 50 linhas com **só o `negocio_id` e a regra violada**. Nenhum valor, nome, e-mail nem proprietário sai no resumo da execução (dado do cliente).
- A decisão de **corrigir na origem** ou **rever a regra** é da Alupar e do Ricardo, e não é tomada aqui. Este trabalho só traz o dado.
- Não se afrouxa a asserção.

### 2.2 `google-api-core` (item 2)
- Atualização por `uv lock --upgrade-package google-api-core`. Medido em 23/10: 2.35.0 para 2.43.0, e entra `opentelemetry-api` como dependência nova. A suíte inteira e o `pip-audit` decidem se fica.
- Na execução o `pip-audit` reprovou `filelock` 3.32.4 (CVE-2026-112940), advisório novo que já estava no lock da `main`; entrou junto, na 4.2.4.

### 2.3 Rede de segurança da conferência (item 3)
- Teste que compara as Silvers em `definitions/silver/` com `SILVER` do `conferir_cargas.py` e com uma constante nova `EXCECOES_DA_CONFERENCIA`. Medido em 23/10: 59 Silvers, 14 na conferência, **45 fora**.
- As 45 entram como exceção declarada, com o motivo escrito: essas fontes são acompanhadas pela `gold.saude_ingestao`, não por contagem de linhas. Fonte nova passa a falhar o teste até alguém decidir.

### 2.4 Testes ignorados (item 4)
- Documento `docs/qualidade/testes-ignorados.md`: motivo, quantidade e exemplo, a partir de `pytest -rs`. Se algum motivo não for "falta credencial ou ambiente", cada grupo vira uma issue com o nome do arquivo.

### 2.5 Documentação do CI e CD (item 5)
- `docs/runbook/deploy.md` ganha: o gatilho `alupdata-deploy` e suas substituições, os agendados (todos desligados por padrão) e como ligar a atribuição (D1) e o painel (D2).

## 3. Fora do escopo
- Qualquer mudança de IAM, de produção ou de dado em BigQuery.
- Reabrir as decisões das ADRs 027 a 030.

## 4. Critérios de aceite
- `uv run pytest tests -q`, `ruff`, `terraform fmt` e `bandit` verdes; os checks do PR (inclusive o do Cloud Build) verdes.
- Disparo de `Conferir cargas` em dev e hml mostra os dois itens do Hubspot.
- O `pip-audit` passa com o `uv.lock` novo.
