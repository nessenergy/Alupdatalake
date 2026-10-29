# Atualização de documentos, painéis e apresentação do sprint de 29/10 — plano

> **Para quem executa:** usar superpowers:executing-plans. Passos com caixa de seleção.

**Objetivo:** alinhar documentos, painel vivo e quadro do GitHub ao estágio de 29/10/2026 e entregar uma apresentação simples para o sprint semanal.

**Arquitetura:** só documentação e dados do painel. O painel lê `painel/marcos.toml` e o publica pelo workflow `Painel`; o quadro (Project 2) sincroniza pelo workflow `Quadro`. A apresentação reaproveita o modelo de `docs/apresentacoes/estado-15-09.html`.

**Fonte:** medições e execuções de 27 a 29/10 registradas em `docs/status.md`.

## Restrições globais

- Comentários, docs e commits em português; sem atribuição a ferramenta de IA em nada publicado (regra 6).
- Nenhum número sem origem: o que não foi medido sai escrito como não medido.
- Nenhum dado real de cliente em documento ou apresentação.

### Tarefa 1: conferência do BBCE

**Arquivos:** `scripts/conferir_cargas.py`, `tests/unit/test_conferir_cargas.py`

- [x] BBCE entra na conferência da Silver e `curva_forward_vigente` na da Gold, com teste (#437).
- [x] Rodar `Conferir cargas` em dev e hml: Silver 254 nos dois; Gold 254 em dev e 0 em hml (Dataform ainda não rodou em hml após a carga).

### Tarefa 2: documentos

**Arquivos:** `docs/status.md`, `docs/proximos-passos.md`, `docs/visao-consolidada.md`, `docs/dicionario-dados/bbce_curva_forward.md`

- [x] Seção "Atualização de 29/10/2026" no `status.md` e data do cabeçalho.
- [x] Visão consolidada: Onda 2, números de teste (2.138 aprovados, 537 ignorados) e quem depende de quem.
- [x] Dicionário do BBCE: `Bearer <idToken>` e `accessToken` na query.

### Tarefa 3: painel

**Arquivos:** `painel/marcos.toml`

- [x] Item 2.2 (BBCE) para 90% e dois marcos novos (27 e 28/10).
- [ ] Depois do merge, rodar o workflow `Painel` e o `Quadro` e conferir a URL.

### Tarefa 4: apresentação

**Arquivos:** `docs/apresentacoes/sprint-29-10.html`

- [x] Seis telas: capa, entregas, números, custo, pendências e próximos passos.

### Tarefa 5: verificação e entrega

- [x] `uv run pytest tests/unit`: 2.138 aprovados, 537 ignorados.
- [ ] PR, 9 checks verdes, merge, e disparo dos workflows `Painel` e `Quadro`.
