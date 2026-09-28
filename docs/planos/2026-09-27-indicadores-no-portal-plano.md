# Plano: indicadores proporcionais no Portal

**Desenho:** [`2026-09-27-indicadores-no-portal.md`](2026-09-27-indicadores-no-portal.md).
Este plano executa o desenho. Onde o desenho deixou ponto em aberto (§7), vale
a decisão registrada abaixo, e cada uma pode ser trocada antes da execução.

**Objetivo:** cinco razões técnicas do setor, calculadas no Dataform numa Gold
nova e mostradas no Portal, cada uma com numerador e denominador explícitos.

**Arquitetura:** `definitions/gold/indicadores_mensais.sqlx` (Dataform, tipo
`table`) lê cinco Gold de domínio que já existem. `src/portal/dados.py` ganha
`indicadores()` nos dois provedores, e `src/portal/app.py` ganha a rota
`/indicadores`. Nenhuma Gold de domínio muda.

**Tecnologias:** Dataform (SQLX), Flask, pytest, sqlglot (já usado em
`tests/unit/test_sql.py`). Nenhuma dependência nova.

## Decisões sobre os pontos em aberto do desenho

| # | Ponto | Decisão | Se estiver errada |
|---|---|---|---|
| 1 | Histórico de 24 meses | **fora deste plano**: reprocessar roda jobs e varre o BigQuery no GCP da Alup, e isso é custo dela. Fica como Tarefa 5, **só com aprovação** | a tela nasce com 2 a 4 meses por indicador, o que já mostra o formato |
| 2 | Domínio no catálogo | `planejamento`, com os três gestores da Comercialização como responsáveis, como no B1 | trocar o valor no mapa de `scripts/anotar_catalogo.py` e reaplicar |
| 3 | Mês-base do PLD real | o último mês com IPCA publicado | trocar a CTE `base` |
| 4 | Quando mostrar à Alup | construir em `dev` e `hml` e apresentar na reunião de aceite | nada a desfazer: o acesso já é o do IAP |

## Restrições globais

- **Regra 6:** sem atribuição de IA em commit, PR, comentário ou documento.
  Validar com `python scripts/verifica_atribuicao.py .git/MSG`.
- **TDD:** teste antes do código.
- **Nomes e textos:** código em inglês onde já é convenção; nomes de objeto e
  coluna em `snake_case` sem acento; textos e comentários em português.
- **Gold de domínio continua sem razão** (ADR 012). A única tabela com divisão
  entre séries é `indicadores_mensais`, e um teste passa a garantir isso.
- **Publicação:** nada vai ao GitHub antes do aval do Ricardo sobre o desenho,
  porque o tema KPI é sensível no contrato.

---

### Tarefa 1: a Gold `indicadores_mensais`

**Arquivos:**
- Criar: `definitions/gold/indicadores_mensais.sqlx`
- Modificar: `tests/unit/test_sql.py`

- [ ] **Passo 1: testes.** Em `tests/unit/test_sql.py`:

```python
INDICADORES = (DEFINICOES / "gold" / "indicadores_mensais.sqlx")
NOMES_DE_INDICADOR = {"taxa_corte_renovavel", "disponibilidade", "fator_capacidade", "armazenamento", "pld_real"}


def test_indicadores_declara_os_cinco_indicadores_e_as_assercoes():
    sql = INDICADORES.read_text(encoding="utf-8")
    corpo = _sem_comentarios(sql)

    for nome in NOMES_DE_INDICADOR:
        assert f"'{nome}' AS indicador" in corpo, nome
    assert 'uniqueKey: ["periodo_apuracao", "indicador", "submercado", "fonte"]' in sql
    assert "denominador > 0" in sql
    assert "SAFE_DIVIDE(numerador, denominador)" in corpo


def test_so_indicadores_mensais_divide_uma_serie_por_outra():
    """ADR 012: razão mora numa tabela só, rotulada como tal; Gold de domínio agrega."""
    for arquivo in (DEFINICOES / "gold").glob("*.sqlx"):
        if arquivo.stem == "indicadores_mensais":
            continue
        assert "SAFE_DIVIDE(" not in _sem_comentarios(arquivo.read_text(encoding="utf-8")), arquivo.name
```

  O segundo teste pode encontrar `SAFE_DIVIDE` já usado em Gold de domínio
  para média ou fração publicada pela origem (como `fracao_coberta`). Nesse
  caso, a lista de exceções vira explícita no teste, com o motivo ao lado de
  cada item, em vez de afrouxar a regra.

- [ ] **Passo 2:** `uv run pytest tests/unit/test_sql.py -q` e confirmar a
  falha, porque o `.sqlx` ainda não existe.

- [ ] **Passo 3: o `.sqlx`.**

```sql
config {
  type: "table",
  schema: "gold",
  tags: ["gold"],
  dependOnDependencyAssertions: true,
  assertions: {
    uniqueKey: ["periodo_apuracao", "indicador", "submercado", "fonte"],
    nonNull: ["periodo_apuracao", "indicador", "numerador", "denominador"],
    rowConditions: [
      "denominador > 0",
      "unidade_valor != 'fração' OR valor BETWEEN 0 AND 1"
    ]
  }
}

-- Gold: razões técnicas do setor, com numerador e denominador explícitos.
--
-- Única Gold que divide uma série por outra (ADR 012, adendo de 27/09). São
-- razões de definição física ou regulatória, sem meta nem fórmula de negócio
-- da Alup; indicador com meta é Fase 2. Formato longo: indicador novo não muda
-- o schema e a tela do Portal lê tudo do mesmo jeito.

WITH
corte AS (
  SELECT
    periodo_apuracao,
    'taxa_corte_renovavel' AS indicador,
    submercado,
    tecnologia AS fonte,
    SUM(soma_nao_gerado_mw_meia_hora) AS numerador,
    'não gerado (MW por meia hora)' AS unidade_numerador,
    SUM(soma_gerado_mw_meia_hora) + SUM(soma_nao_gerado_mw_meia_hora) AS denominador,
    'potencial: gerado + não gerado (MW por meia hora)' AS unidade_denominador,
    'fração' AS unidade_valor,
    COUNT(*) AS itens_na_base
  FROM ${ref("gold", "restricao_coff_mensal_usina")}
  GROUP BY periodo_apuracao, submercado, tecnologia
),

disponibilidade AS (
  SELECT
    periodo_apuracao,
    'disponibilidade' AS indicador,
    submercado,
    tipo_usina AS fonte,
    SUM(disponibilidade_media_mw) AS numerador,
    'disponibilidade média (MW)' AS unidade_numerador,
    SUM(potencia_instalada_mw) AS denominador,
    'potência instalada (MW)' AS unidade_denominador,
    'fração' AS unidade_valor,
    COUNT(*) AS itens_na_base
  FROM ${ref("gold", "disponibilidade_mensal_usina")}
  WHERE disponibilidade_media_mw IS NOT NULL AND potencia_instalada_mw > 0
  GROUP BY periodo_apuracao, submercado, tipo_usina
),

-- Agregado por submercado × tipo, não usina a usina: eólica e solar trazem CEG
-- em só 7% das linhas (o ONS publica por conjunto). A potência é a vigente;
-- mês antigo usa a capacidade de hoje, e a coluna de unidade diz isso.
capacidade AS (
  SELECT submercado, tipo_usina, SUM(potencia_efetiva_total) AS potencia_mw
  FROM ${ref("gold", "capacidade_instalada_vigente_usina")}
  GROUP BY submercado, tipo_usina
),
fator AS (
  SELECT
    g.periodo_apuracao,
    'fator_capacidade' AS indicador,
    g.submercado,
    g.tipo_usina AS fonte,
    SUM(g.geracao_mw_media_horaria) AS numerador,
    'geração média (MW médio)' AS unidade_numerador,
    ANY_VALUE(c.potencia_mw) AS denominador,
    'potência efetiva vigente (MW)' AS unidade_denominador,
    'fração' AS unidade_valor,
    COUNT(*) AS itens_na_base
  FROM ${ref("gold", "geracao_mensal_usina_ons")} AS g
  JOIN capacidade AS c USING (submercado, tipo_usina)
  GROUP BY g.periodo_apuracao, g.submercado, g.tipo_usina
),

armazenamento AS (
  SELECT
    periodo_apuracao,
    'armazenamento' AS indicador,
    submercado,
    CAST(NULL AS STRING) AS fonte,
    ear_media_mwmes AS numerador,
    'energia armazenada média (MWmês)' AS unidade_numerador,
    ear_media_mwmes / (ear_media_percentual / 100) AS denominador,
    'capacidade de armazenamento (MWmês)' AS unidade_denominador,
    'fração' AS unidade_valor,
    1 AS itens_na_base
  FROM ${ref("gold", "armazenamento_e_afluencia_mensal")}
  WHERE ear_media_percentual > 0
),

-- IPCA em % ao mês. Índice encadeado; o mês-base é o último com IPCA.
indice AS (
  SELECT
    periodo_apuracao,
    EXP(SUM(LN(1 + ipca_mes / 100)) OVER (ORDER BY periodo_apuracao)) AS indice
  FROM ${ref("gold", "inflacao_mensal")}
),
base AS (
  SELECT periodo_apuracao AS mes_base, indice AS indice_base
  FROM indice
  QUALIFY ROW_NUMBER() OVER (ORDER BY periodo_apuracao DESC) = 1
),
pld_real AS (
  SELECT
    p.periodo_apuracao,
    'pld_real' AS indicador,
    p.submercado,
    CAST(NULL AS STRING) AS fonte,
    p.pld_medio_reais_mwh AS numerador,
    'PLD médio nominal (R$/MWh)' AS unidade_numerador,
    i.indice / b.indice_base AS denominador,
    'fator de inflação até o mês-base (IPCA)' AS unidade_denominador,
    CONCAT('R$/MWh de ', b.mes_base) AS unidade_valor,
    1 AS itens_na_base
  FROM ${ref("gold", "pld_mensal_submercado")} AS p
  JOIN indice AS i USING (periodo_apuracao)
  CROSS JOIN base AS b
),

unido AS (
  SELECT * FROM corte
  UNION ALL SELECT * FROM disponibilidade
  UNION ALL SELECT * FROM fator
  UNION ALL SELECT * FROM armazenamento
  UNION ALL SELECT * FROM pld_real
)

SELECT
  periodo_apuracao,
  indicador,
  submercado,
  fonte,
  numerador,
  unidade_numerador,
  denominador,
  unidade_denominador,
  SAFE_DIVIDE(numerador, denominador) AS valor,
  unidade_valor,
  itens_na_base
FROM unido
```

- [ ] **Passo 4:** `uv run pytest tests/unit/test_sql.py -q`. Os testes
  existentes (tipo e dataset da camada, dependência de asserções da Gold, SQL
  válido no dialeto BigQuery) passam junto.

- [ ] **Passo 5: conferir o dado, antes do Portal.** Depois do deploy em
  `dev`, rodar:

```sql
SELECT indicador, COUNT(*) linhas, MIN(periodo_apuracao), MAX(periodo_apuracao),
       MIN(valor), MAX(valor)
FROM gold.indicadores_mensais GROUP BY 1 ORDER BY 1
```

  Esperado: cinco indicadores, frações entre 0 e 1 e PLD real na faixa do PLD
  nominal. Se o fator de capacidade passar de 1, a potência vigente está
  subestimando algum tipo, e o indicador sai da tela até a causa ser
  explicada.

- [ ] **Passo 6:** commit
  `feat(gold): indicadores_mensais com razoes tecnicas do setor`.

### Tarefa 2: classificar a Gold no catálogo

**Arquivos:** `scripts/anotar_catalogo.py`, `docs/arquitetura/dominios-analiticos.md`.

- [ ] **Passo 1:** `uv run pytest tests/unit/test_anotar_catalogo.py -q`
  deve falhar: `test_toda_gold_do_dataform_e_anotada_ou_declarada_operacional`
  encontra a Gold nova sem classificação.
- [ ] **Passo 2:** em `dominios-analiticos.md`, domínio 8 · Planejamento,
  trocar **Gold hoje** `—` por `` `indicadores_mensais` ``.
- [ ] **Passo 3:** em `ANOTACOES`, acrescentar:

```python
    # 8 · Planejamento — razões técnicas que atravessam domínios (ADR 012, adendo de 27/09)
    "indicadores_mensais": {
        "dominio": "planejamento",
        "responsavel": "gestores da Comercialização: Letícia Ferreira, Tahigo Santos e Taina Mota",
    },
```

- [ ] **Passo 4:** os testes passam. Commit
  `feat(catalogo): classifica indicadores_mensais em planejamento`.

### Tarefa 3: a tela `/indicadores`

**Arquivos:** `src/portal/dados.py`, `src/portal/app.py`, `tests/unit/test_portal.py`.

**Interfaces:**
- `dataclass Indicador(periodo_apuracao: str, indicador: str, submercado: str | None, fonte: str | None, numerador: Decimal, unidade_numerador: str, denominador: Decimal, unidade_denominador: str, valor: Decimal | None, unidade_valor: str)`
- `ProvedorDados.indicadores(self, meses: int = 12) -> list[Indicador]`

- [ ] **Passo 1: testes**, no padrão de `test_portal.py` e com o provedor
  simulado:

```python
def test_indicadores_mostra_os_cinco_com_numerador_e_denominador(cliente) -> None:
    corpo = cliente.get("/indicadores").get_data(as_text=True)
    for titulo in ("Taxa de corte renovável", "Disponibilidade", "Fator de capacidade", "Armazenamento", "PLD real"):
        assert titulo in corpo
    assert "potência instalada (MW)" in corpo  # o denominador aparece, não só o valor


def test_indicadores_simulado_e_rotulado(cliente) -> None:
    assert "dados de exemplo" in cliente.get("/indicadores").get_data(as_text=True)


def test_barra_de_navegacao_tem_indicadores(cliente) -> None:
    assert 'href="/indicadores"' in cliente.get("/").get_data(as_text=True)
```

- [ ] **Passo 2:** confirmar a falha (404 na rota).
- [ ] **Passo 3: provedores.**
  - `ProvedorSimulado.indicadores`: poucas linhas inventadas, uma por
    indicador × dois meses, rotuladas como exemplo como no resto do simulado.
  - `ProvedorBigQuery.indicadores`: `SELECT * FROM gold.indicadores_mensais`,
    com os últimos `@meses` meses em parâmetro de consulta, sem interpolar
    entrada (mesmo padrão de `volumetria`).
- [ ] **Passo 4: rota e página.**
  - `@app.get("/indicadores")` no molde de `/custo`.
  - `_pagina_indicadores(linhas, usuario, simulado)`: uma seção por indicador,
    na ordem da tabela do desenho, com título, uma frase do que mede e uma
    tabela de recortes (`submercado · fonte`) × meses.
  - Fração vira `%` com uma casa; PLD real em R$ com duas casas (D7).
  - Célula com `title="numerador unidade ÷ denominador unidade"`; o cabeçalho
    da seção repete as unidades por extenso, para quem não passa o mouse.
  - `_naves` ganha `("/indicadores", "Indicadores")`.
  - Todo texto vindo do dado passa por `html.escape`.
- [ ] **Passo 5:** `uv run pytest tests/unit/test_portal.py -q` verde; olhar a
  tela local com `uv run flask --app src.portal.app run`.
- [ ] **Passo 6:** commit `feat(portal): tela de indicadores proporcionais`.

### Tarefa 4: registros

- [ ] **ADR 005, adendo de 27/09:** a tela `/indicadores` entra pelo mesmo
  motivo da `/lake` e da `/custo`. Ela prova o caminho e não substitui o BI.
  Continuam fora filtros, exportação e meta.
- [ ] **ADR 012, adendo de 27/09:** razão técnica do setor não é KPI. Ela mora
  só em `indicadores_mensais`, e um teste garante isso. A leitura depende de
  **aceite por escrito da Alup**, pedido na reunião de aceite.
- [ ] `docs/status.md` e `painel/marcos.toml`, item 4.4: as Gold consolidadas
  passam a ter um primeiro entregável. Rodar `uv run pytest tests/ -q` e fazer
  o commit.

### Tarefa 5 (só com aprovação): histórico de 24 meses

- Reprocessar as janelas antigas das seis fontes que alimentam os
  indicadores, pelo workflow **Executar ingestão**, uma fonte por vez, em
  `dev`.
- Antes de rodar, estimar os bytes varridos com o `dry_run` do BigQuery e
  levar o número ao Ricardo. O custo é da Alup, sob o teto da E2.

## Aceite

- `uv run pytest tests/ -q` verde, sem afrouxar teste existente.
- Em `dev`: `gold.indicadores_mensais` com os cinco indicadores, as asserções
  do Dataform passando e `/indicadores` mostrando o dado real.
- Catálogo: a tabela anotada em `planejamento` pelo deploy.
- Nada publicado no GitHub antes do aval do Ricardo.
