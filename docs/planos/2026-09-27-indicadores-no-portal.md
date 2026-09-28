# Desenho: indicadores proporcionais no Portal

**Estado:** rascunho para revisão interna da ness. Não autoriza código nem
publicação. Depois de aprovado, vira plano de execução (`writing-plans`).

**Pedido (27/09):** definir KPIs **proporcionais** nos dois sentidos, razão
entre duas grandezas e conjunto do tamanho da Fase 1, e decidir como
consumi-los. Consumidor escolhido: o **Portal Alup**.

## 1. Restrições que o desenho respeita

- **ADR 012 — KPI fora da Fase 1**, por decisão da Alup (A5, A6). O desenho só
  calcula **razão técnica do setor**, com definição regulatória ou física e
  sem meta, sem comparação entre coligadas e sem fórmula de negócio da Alup. A
  leitura "razão técnica não é KPI" precisa de **aceite por escrito** da Alup,
  e o lugar natural é a reunião de aceite (~01/10).
- **ADR 005 — o Portal não é o consumidor final**, e telas novas viram
  mudança de escopo formal. Precedentes: `/lake` (ADR 006) e `/custo`
  (FinOps). A tela `/indicadores` entra como **adendo à ADR 005**, com a mesma
  justificativa: prova o caminho da Gold até o usuário e não substitui o BI.
- **A conta mora na Gold (ADR 012), não no Portal.** Assim o Power BI ou o
  front da Fase 2 lê a mesma tabela, sem reimplementar a fórmula.

## 2. Abordagem escolhida

**A — razões calculadas no Dataform, lidas pelo Portal.** Uma Gold nova,
`gold.indicadores_mensais`, e uma rota `/indicadores` que só lê essa tabela.
Descartadas: (B) SQL de razão dentro de `src/portal/dados.py`, que prende a
fórmula ao Portal; (C) view solta no BigQuery, que foge do Dataform.

## 3. Os indicadores

Cada linha guarda **numerador e denominador**, não só o resultado: é isso que
faz o indicador ser proporcional e auditável.

| Indicador | Numerador ÷ denominador | Recorte | Fonte na Gold | Situação do dado (27/09, `dev`) |
|---|---|---|---|---|
| `taxa_corte_renovavel` | não gerado ÷ (gerado + não gerado), somas de MW por meia hora | submercado × eólica/solar | `restricao_coff_mensal_usina` | **pronto**: 12% a 51% por submercado em 09/2026. A unidade se cancela, então não é preciso converter MW em MWh |
| `disponibilidade` | disponibilidade média (MW) ÷ potência instalada (MW) | submercado × tipo (UHE, UTE, UTN) | `disponibilidade_mensal_usina` | **pronto**: as duas grandezas estão na mesma linha |
| `fator_capacidade` | geração média (MWmed) ÷ potência efetiva (MW) | submercado × tipo | `geracao_mensal_usina_ons`, `capacidade_instalada_vigente_usina` | **com ressalva**: agregado por submercado × tipo, não usina a usina, porque eólica e solar trazem CEG em só 7% das linhas. A potência é a **vigente**, e meses antigos usam a capacidade de hoje |
| `armazenamento` | EAR média (MWmês) ÷ capacidade (MWmês) | submercado | `armazenamento_e_afluencia_mensal` | **pronto**: a capacidade sai da própria linha (EAR ÷ EAR %) |
| `pld_real` | PLD médio (R$/MWh) ÷ fator do IPCA acumulado até o mês-base | submercado | `pld_mensal_submercado`, `inflacao_mensal` | **histórico curto**: 3 meses de IPCA e de PLD |
| `cobertura_exposicao` | cobertura ÷ exposição negativa (R$) | mercado | `exposicao_mercado_mensal` | **fora por ora**: 100% em todos os meses carregados, então não informa. Volta se aparecer variação |

**Fica de fora de propósito:** balanço contratual por perfil. Com dado
público, ele mostra a posição de qualquer agente, e expor isso num painel da
Alup sem finalidade definida é risco, não indicador.

**Primeiro candidato da Fase 2:** os mesmos indicadores **por usina do
portfólio da Alup**. Depende da lista de usinas deles (Onda 3/FMB) e é onde
passam a fazer sentido meta e comparação entre coligadas.

## 4. A tabela `gold.indicadores_mensais`

Formato longo, uma linha por período × indicador × recorte, para a tela ser
genérica e indicador novo não mudar schema:

| Coluna | Tipo | Conteúdo |
|---|---|---|
| `periodo_apuracao` | STRING | `AAAA-MM` |
| `indicador` | STRING | um dos cinco nomes acima |
| `submercado` | STRING | N, NE, S, SE ou NULL |
| `fonte` | STRING | tipo de geração, ou NULL |
| `numerador` | NUMERIC | |
| `unidade_numerador` | STRING | por extenso, como `MW médio` |
| `denominador` | NUMERIC | |
| `unidade_denominador` | STRING | |
| `valor` | NUMERIC | `SAFE_DIVIDE(numerador, denominador)`, sem arredondar |
| `unidade_valor` | STRING | `fração` ou `R$/MWh de <mês-base>` |
| `itens_na_base` | INT64 | quantas usinas ou linhas entraram na soma |

**Asserções do Dataform:**
- chave única (`periodo_apuracao`, `indicador`, `submercado`, `fonte`);
- `denominador > 0`;
- `valor BETWEEN 0 AND 1` quando `unidade_valor = 'fração'`.

**Catálogo:** a tabela entra no mapa de `scripts/anotar_catalogo.py`. O
domínio fica em aberto (ver §7).

## 5. A tela `/indicadores`

- **Formato:** HTML renderizado no servidor, como `/lake` e `/custo`, sem
  framework novo.
- **Conteúdo:** uma seção por indicador, com uma frase do que ele mede e uma
  tabela de recortes (linhas) × últimos 12 meses (colunas). O valor aparece
  em %, com numerador e denominador no título da célula. Cada linha tem uma
  tendência pequena, feita com o `src/portal/grafico.py` que já existe.
- **Sem:** filtros, exportação ou meta, que continuam fora (ADR 005).
- **Provedor simulado:** traz dados de exemplo rotulados na tela, como as
  outras rotas.
- **Acesso:** o mesmo IAP (`portal_acesso`); nada muda na autenticação.

## 6. Testes

- Unitários do SQL, no padrão de `tests/unit/test_sql.py`: tipo `table`,
  asserções presentes e os cinco indicadores declarados.
- Da tela, com o provedor simulado: rota responde, cada indicador aparece,
  numerador e denominador estão na célula.
- `test_anotar_catalogo.py`: a Gold nova precisa estar classificada, como
  qualquer outra.

## 7. Em aberto (decidir antes do plano)

1. **Histórico.** Com 3 meses, a tendência de 12 meses fica quase vazia. O
   conserto é reprocessar janelas antigas das fontes públicas (regra 3: é só
   passar outra janela). Custo: tempo de job e varredura no BigQuery da Alup.
   Proposta: 24 meses de PLD, IPCA, carga, EAR, geração e disponibilidade,
   como tarefa própria do plano.
2. **Domínio da tabela no catálogo.** Ela atravessa domínios. Opções:
   classificar como `planejamento` (hoje vazio), ou criar o valor
   `transversal`, o que muda o enum do aspect type.
3. **Mês-base do PLD real.** Proposta: o último mês com IPCA publicado, para o
   valor ler como "em reais de hoje".
4. **Quando mostrar à Alup.** Proposta: construir e publicar em `dev` e `hml`,
   e apresentar na reunião de aceite junto com o pedido de aceite da leitura da
   ADR 012.
