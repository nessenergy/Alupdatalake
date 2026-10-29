# Pendências da Alup e painel vivo: corrigir o que não é verdade — plano

> **Para quem executa:** usar superpowers:executing-plans. Passos com caixa de seleção.

**Objetivo:** tirar do painel e do GitHub as pendências da Alupar que já foram resolvidas (o aceite das Ondas 0 e 1 está assinado e faturado) e deixar o painel vivo coerente com o estado de 29/10/2026.

**Arquitetura:** o painel tem duas fontes. As pendências vêm das issues abertas com a etiqueta `tipo/dependencia` (lidas pelo `scripts/painel.py` a cada 3 horas); os marcos, as ondas e o progresso vêm de `painel/marcos.toml`. O `dados.json` publicado já é de hoje (gerado às 15h25), então o problema é de conteúdo, não de publicação: issues que ninguém fechou e marcos "previstos" com data vencida.

**Fonte dos fatos:** `docs/status.md` (atualizações de 13/10, 22/10, 27/10 e 29/10) e os comentários das issues.

## Restrições globais

- Comentários, docs e commits em português; sem atribuição a ferramenta de IA em nada publicado, incluindo comentário de issue (regra 6; a checagem automática não cobre issue, conferir à mão).
- Só se fecha issue com evidência escrita no comentário. O que não está provado fica aberto.
- Nada de dado real de cliente.

## O que o painel publicado mostra hoje (medido em 29/10 no `dados.json`)

| Item | Mostra | Fato |
|---|---|---|
| Pendência #258 "Quem assina o aceite" | atrasada (prazo 29/09) | Eduardo Pires aprovou por escrito em 05/10; marcos 1 e 2 faturados (R$ 53.760) |
| Pendência #262 "Credenciais da Onda 2: Hubspot e BBCE" | atrasada (prazo 12/10) | Hubspot gravado em 20/10; BBCE funcionando em 28/10 |
| Pendência #260 "32h do item 2.1" | atrasada (prazo 30/09) | Alupar respondeu em 20 e 27/10: CCEE por SOAP; falta gravar os valores e confirmar o escopo |
| Pendências #174 e #129 (TempoOK) | abertas | TempoOK fora do escopo (20/10, confirmado em 27/10) |
| Pendência #87 (billing e alertas) | aberta | Destinatários em 11/09; conta de faturamento vinculada em 23/09; teto respondido em 01/10 |
| Marco 03/10 CPTEC "bloqueado" | previsto | CPTEC entregue em 22/10 e retirado do escopo em 23/10 |
| Marco 12/10 credenciais (prazo interno) | previsto | superado pelos marcos de 20/10 e 27/10 |
| Marco 16/10 "Fim da janela da Onda 1 (marco 2)" | previsto | Onda 1 aceita e faturada em 05/10 |
| Marcos 03/10 ONS e INMET | previstos | cargas conferidas em 03/10 |

---

### Tarefa 1: encerrar no GitHub as pendências comprovadamente resolvidas

**Arquivos:** nenhum no repositório; issues #258, #262, #174, #129 e #87.

- [ ] **Passo 1:** para cada issue, escrever o comentário com o fato e a fonte, sem rodapé de ferramenta. Exemplo da #258:

```bash
gh issue comment 258 --body "Encerrada. Eduardo Pires aprovou por escrito as Ondas 0 e 1 em 05/10/2026 e os marcos 1 e 2 (R\$ 53.760,00) foram faturados. Registro em docs/status.md, atualização de 13/10."
gh issue close 258 --reason completed
```

- [ ] **Passo 2:** repetir para #262 (Hubspot gravado em 20/10; BBCE em uso em 28/10, status.md de 27/10), #174 e #129 (TempoOK fora do escopo, 20/10, confirmado em 27/10; `--reason "not planned"`) e #87 (destinatários 11/09, conta de faturamento vinculada 23/09, teto 01/10; o valor do orçamento por ambiente é item da ness., 2.13).
- [ ] **Passo 3:** conferir que nenhum comentário tem `Co-Authored-By`, "Generated" ou emoji de robô: `gh issue view N --json comments --jq '.comments[-1].body'`.

### Tarefa 2: ajustar as pendências que continuam reais

**Arquivos:** issues #11, #260, #14 e #15.

- [ ] **Passo 1:** #11 (tokens CCEE, BBCE, Hubspot, TempoOK): trocar o título para "Gravar os valores da ONS e da CCEE nos segredos" e comentar o que já foi resolvido (BBCE, Hubspot, TempoOK).
- [ ] **Passo 2:** #260: comentar a resposta da Alupar (CCEE por SOAP, usuário, senha e certificado) e o que falta (valores, formato do certificado, confirmação das 32 h). Ler antes `_prazo` em `scripts/painel.py:194` para saber qual `Prazo:` o painel lê, e só escrever prazo que exista no contrato.
- [ ] **Passo 3:** #14 (MySQL Comercialização conecta desde 19/10; falta a lista de tabelas) e #15 (RM/TOTVS: a Alupar não tem endpoints; precisa dos dados de faturamento, 27/10).
- [ ] **Passo 4:** deixar #12, #13, #16, #57, #141, #142 e #150 como estão: não há evidência nova para fechá-las, e o estado de cada uma já consta em `docs/status.md`.

### Tarefa 3: marcos do painel

**Arquivos:** `painel/marcos.toml`; teste: `tests/unit/test_painel.py`.

- [ ] **Passo 1:** ler os valores de `estado` aceitos em `carregar_marcos` (`scripts/painel.py:46`) antes de editar.
- [ ] **Passo 2:** em `painel/marcos.toml`:
  - o marco de 16/10 passa a "Marco 2 da Onda 1 (R$ 30.720) aprovado em 05/10 e faturado", `estado = "feito"`;
  - o marco de 12/10 (credenciais) é removido e o de 19/10 é reescrito: Hubspot (20/10) e BBCE (28/10) resolvidos; ONS e CCEE aguardam os valores;
  - o marco de 03/10 do CPTEC é removido (já há os de 22/10 e 23/10);
  - os de 03/10 do ONS e do INMET passam a `feito`, mantendo a ressalva da regra provisória da ADR 026 e da 027 no texto;
  - novo marco com a data de hoje: "Pendências de aceite encerradas no GitHub".
- [ ] **Passo 3:** `uv run pytest tests/unit/test_painel.py -q` deve passar.

### Tarefa 4: documentos

**Arquivos:** `docs/status.md`, `docs/proximos-passos.md`.

- [ ] **Passo 1:** na seção de 29/10 do `status.md`, acrescentar o encerramento das issues (números) e dizer que o aceite de 05/10 está faturado.
- [ ] **Passo 2:** em `docs/proximos-passos.md`, as linhas 29–46, 87 e 230 falam de aceite pendente. Ler o contexto de cada uma; se for texto de situação passada com data, deixar; se for lista de pendências atuais, corrigir.
- [ ] **Passo 3:** `git grep -n "nenhuma onda está aceita"`: só pode restar em seção datada de 02/10.

### Tarefa 5: publicar e conferir

- [ ] **Passo 1:** PR com `docs:` e `chore:` (sem trailer de atribuição), 9 checks verdes, merge.
- [ ] **Passo 2:** `gh workflow run Painel` e acompanhar até `success`.
- [ ] **Passo 3:** abrir `https://painel.alupdata.ness.com.br/dados.json` e confirmar: `pendencias` sem #258, #262, #174, #129 e #87; nenhum marco `previsto` com data anterior a hoje, exceto os que ainda dependem da Alupar.
- [ ] **Passo 4:** conferir também a página `https://painel.alupdata.ness.com.br/` (leitura visual das pendências e dos marcos).

## Revisão do plano

- Cobertura: aceite (T1, T3, T4), painel desatualizado (T3, T5), pendências reais mantidas (T2).
- Risco: fechar issue é visível para a Alupar. Por isso cada fechamento leva a evidência no comentário e nada é fechado sem fonte no repositório.
- Fora do plano: o item 2.4 (TempoOK, 18 h, 80% pronto) continua contando no progresso das 580 h. Se o TempoOK saiu do escopo, a conta das horas muda; isso é decisão contratual e fica com o Ricardo.
