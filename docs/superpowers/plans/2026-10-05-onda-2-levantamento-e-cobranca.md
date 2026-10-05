# Onda 2 — levantamento e rascunho de cobrança das credenciais — Implementation Plan

> **Para agentes:** use superpowers:subagent-driven-development ou superpowers:executing-plans. Passos com checkbox.

**Goal:** (1) dizer, fonte a fonte, o que a Onda 2 já tem e o que falta para os 7 componentes, separando o que depende de credencial da Alup do que não depende; (2) deixar pronto, sem enviar, o rascunho de cobrança das credenciais que o plano manda registrar.

**Architecture:** só leitura do repositório (item 1) e um rascunho de e-mail no Gmail (item 2). Nenhum código de conector, nenhuma fonte nova, nenhuma mudança de infraestrutura.

**Tech Stack:** `git grep` e `ls` sobre o repositório, Markdown, rascunho HTML no Gmail.

**Spec:** `docs/plano-execucao.md` §4 (Onda 2, itens 2.1 a 2.5), `docs/contrato/resumo-contrato.md` (cláusula 3ª, prazos de credencial; marco 3 em 13/11/2026) e `docs/status.md` (credenciais prometidas para 01/10 e não recebidas). Pedido do Ricardo em 05/10/2026: "vamos para frente para a próxima onda", delimitado ao levantamento (1) e ao rascunho de cobrança (2).

## Global Constraints

- Escopo literal: nada além do levantamento e do rascunho. Sem conector novo, sem Gold nova, sem alteração de painel ou de estado de onda.
- **Regra 6:** nenhuma atribuição de ferramenta de IA em commit, PR, documento ou e-mail; validar a mensagem de commit com `python scripts/verifica_atribuicao.py`.
- O rascunho **não é enviado** por este plano. Cobrança, prazo e multa são decisão do Ricardo; o plano só registra fatos e datas.
- Nunca inventar nome de pessoa: usar só os que estão nos e-mails e documentos do repositório (Leonardo, sem sobrenome, como consta em `docs/status.md`).
- Credencial só via Secret Manager; o documento e o e-mail nunca trazem valor de credencial.
- Dado de cliente fora do repositório. Documentos em português; commits convencionais; branch `docs/…`; PR para `main`; mesclar só com CI verde; adicionar arquivos por nome.
- E-mail ao cliente: HTML no padrão do e-mail de 01/10, corpo em peso normal e negrito só em título e cabeçalho de tabela; resposta no fio existente; nunca colar URL com redirecionamento do Google.

---

### Tarefa 1: Levantamento da Onda 2 (item 1)

**Files:**
- Create: `docs/relatorios/2026-10-05-onda-2-levantamento.md`

**Interfaces:**
- Consumes: itens 2.1 a 2.5 de `docs/plano-execucao.md` §4 e os 7 componentes da cláusula 2ª (conector, Bronze, Silver, Gold, testes, agendamento, documentação com linhagem).
- Produces: uma tabela fonte × componente e uma lista "o que falta e por quê".

- [ ] **Passo 1: fixar o critério do item 2.5.** Ler em `docs/contrato/` e no plano o texto exato do item "Tabelas Gold de preço e posição comercial" e copiá-lo para o relatório entre aspas. O levantamento mede o 2.5 **contra esse texto**, não contra uma interpretação.
- [ ] **Passo 2: levantar os componentes de cada fonte.** Para cada rótulo abaixo, rodar os comandos e anotar presente ou ausente, com o caminho:

```bash
for f in ccee_agente bbce_curva_forward hubspot_negocios tempook_boletins tempook_arquivos tempook_ena_prevs; do
  echo "== $f"
  ls src/conectores/$f.py 2>&1 | tail -1                          # 1 conector
  ls definitions/bronze/$f.sqlx 2>&1 | tail -1                    # 2 Bronze
  ls definitions/silver/$f.sqlx 2>&1 | tail -1                    # 3 Silver
  git grep -l "$f" -- definitions/gold                            # 4 Gold que consome a Silver
  ls tests/unit/conectores/test_$f.py 2>&1 | tail -1              # 5 testes
  git grep -n "$f" -- infra/modules/scheduler/main.tf | head -2   # 6 agendamento
  ls docs/dicionario-dados/$f.md 2>&1 | tail -1                   # 7 documentação
done
```

Se um rótulo não casar com o nome do arquivo (por exemplo, o conector do agente CCEE ou do boletim com outro nome), procurar o rótulo em `src/conectores/` com `git grep -n "fonte = " src/conectores/<arquivo>.py` e usar o nome real; registrar a correspondência.
- [ ] **Passo 3: separar teste real de teste ignorado.** Para cada fonte, contar quantos testes do arquivo estão ignorados por falta de credencial: `git grep -c "skipif\|pytest.mark.skip" -- tests/unit/conectores/test_<fonte>.py tests/integration`. O relatório diz quais testes só rodam com a credencial real.
- [ ] **Passo 4: dizer o que falta e por quê.** Para cada fonte, uma linha com uma das três classes, e nenhuma outra:
  1. **Completa nos 7 componentes e só falta rodar com a credencial real** (dependente da Alup);
  2. **Falta componente, e dá para fazer sem credencial** (dependente da ness.);
  3. **Falta componente ou escopo e a decisão é da Alup** (por exemplo, o item 2.1, CCEE agente, aguardando a posição da Alup, #260).

  Para o item 2.5, dizer qual das Golds existentes (`curva_forward_vigente`, `exposicao_mercado_mensal`, `pld_mensal_submercado`, `posicao_contratual_mensal_perfil`) atende ao texto do passo 1 e o que sobra, sem criar nada.
- [ ] **Passo 5: escrever o relatório** com: o critério do 2.5 (passo 1), a tabela fonte × 7 componentes (passos 2 e 3), a classe de cada fonte (passo 4), e o estado da credencial segundo `docs/status.md` (segredos do Hubspot e do BBCE sem versão em dev e hml). **Nenhum número entra sem o comando que o gerou.** Citar o prazo interno (12/10) e o contratual (19/10) apenas como constam no repositório.
- [ ] **Passo 6: commit** `docs: levantamento da Onda 2 por fonte e componente`, validando a mensagem; PR; mesclar com CI verde.

### Tarefa 2: Rascunho de cobrança das credenciais (item 2)

**Files:**
- Nenhum arquivo do repositório. O produto é um rascunho no Gmail, no fio das credenciais.

**Interfaces:**
- Consumes: o relatório da Tarefa 1 (o que se pede para cada fonte) e o fio de e-mail com Leonardo sobre as credenciais da Onda 2.
- Produces: um rascunho, sem envio, com os dados da cobrança.

- [ ] **Passo 1: achar o fio.** `search_threads` com `from:leonardo` e as palavras "credenciais", "token" ou "Onda 2", e escolher o fio em que a Alup prometeu as credenciais para 01/10. Se houver mais de um fio plausível, **parar e perguntar ao Ricardo qual usar**; não escolher por conta própria.
- [ ] **Passo 2: escrever o conteúdo, só com fatos verificados.**
  - Quais credenciais faltam, por fonte, como o plano as descreve: CCEE agente credenciado (posição da Alup sobre o caminho e as 32h, #260), BBCE (acesso e host), Hubspot (token de API de private app), TempoOK (conforme o relatório da Tarefa 1).
  - O prazo contratual (19/10/2026, cláusula 3ª) e a data que a Alup indicou (01/10), como constam no repositório.
  - O que a ness. já fez: as fontes estão escritas e testadas contra a documentação; resta ligar e ajustar com a credencial real (conforme o relatório da Tarefa 1).
  - Nenhuma ameaça, nenhuma menção a multa, ociosidade ou suspensão: isso é do Ricardo.
  - Nenhum valor de credencial e nenhum nome de pessoa fora dos que constam no fio.
- [ ] **Passo 3: criar o rascunho** com `create_draft` e `replyToMessageId` do último e-mail do fio, em HTML no padrão do e-mail de 01/10 (bloco com borda ciano, tabela fonte × o que falta, assinatura da ness.), corpo em peso normal, com `body` em texto puro como alternativa. Destinatários e cópias iguais aos do fio.
- [ ] **Passo 4: entregar ao Ricardo** o link do rascunho e a lista do que ele precisa decidir antes de enviar. **Não enviar.** Depois do envio feito por ele, e só então, registrar a data da cobrança em `docs/status.md` (fato e data, nada mais), em PR próprio.

---

## Autoavaliação

**Cobertura:** item 1 = Tarefa 1; item 2 = Tarefa 2. Nada fora deles.

**Placeholders:** a Tarefa 1 traz os comandos; o texto do critério do 2.5 e os nomes reais de alguns conectores só se conhecem lendo os arquivos, e o passo diz como obtê-los. A Tarefa 2 depende de achar o fio (passo 1), com regra de parada se houver ambiguidade.

**Consistência:** a classe de cada fonte (Tarefa 1, passo 4) alimenta o "o que se pede" do rascunho (Tarefa 2, passo 2).

**Riscos:** o levantamento pode mostrar que alguma fonte "completa" tem teste ignorado demais; o relatório só diz, e não corrige. O rascunho depende de eu achar o fio certo; se não achar, aviso.
