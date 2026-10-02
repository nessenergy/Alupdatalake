# ADR 025 — Portal redesenhado para o telão, com modo de rodízio

**Status**: aceito · **Data**: 2026-10-01 · **Complementa** a
[ADR 005](005-escopo-do-portal-mvp.md) (escopo), a
[ADR 006](006-painel-de-saude.md) (painel de saúde) e a
[ADR 022](022-identidade-visual-por-audiencia.md) (identidade da Alup)

## 1. Contexto

O uso principal do Portal na reunião de aceite é o telão, visto a 3 m. As telas
de saúde, indicadores e custo foram feitas para ler de perto: a saúde era um
cartão por fonte, com quatro métricas, um gráfico e o texto do erro — 23 cartões
para responder "o dado está chegando?". Quem olhava o telão não conseguia dizer
se estava tudo bem sem ler todos.

## 2. Decisão

**Saúde do lake.** Um veredito grande no topo (semáforo e frase), um contador por
grupo de origem e uma linha por fonte, com o último sucesso e uma tira de 30 dias.

- O estado de cada fonte vem do Gold (`gold.saude_ingestao`), como na ADR 006: atraso e
  falha recente pedem atenção; fonte que nunca carregou é crítica.
- **Aguardando credencial** é um estado à parte e não pesa no veredito. É decidido
  no Gold: nunca houve sucesso e o último erro é falta de segredo
  (`aguardando_credencial`, regex `secret|cofre local` sobre o erro). Não há lista
  de fontes escrita na tela.
- O grupo é o prefixo do conector (`ons`, `ccee`, `aneel`, `bcb`, `ibge`,
  `tempook`); o que não casa vai para "Outras". Prefixo novo entra em
  `src/portal/saude.py`.
- A tira tem três estados: carregou, sem carga (neutro, não é alarme) e falha. Falha
  só conta no dia em que nada foi carregado: uma nova tentativa que deu certo
  entregou o dado. Não existe "dia sem expectativa", para o Portal não guardar uma
  segunda cópia da cadência de cada fonte (mesma razão da ADR 006). Os dias vêm de
  `gold.volumetria_lake` (`execucoes_com_erro`), sem coluna nova.
- O texto técnico do erro **não aparece mais**: a frase é curta e em português. O
  detalhe fica no log de execução. Revoga a linha "Último erro" da tabela da ADR 006.
- A evidência de entrega das Ondas 0 e 1 continua na página: linhas carregadas no
  total e taxa de sucesso em 30 dias, em um bloco recolhido por fonte. Saem p95 e
  taxa de inválidas.

**Indicadores.** Um cartão por recorte, com o último mês em destaque, a conta à
vista, a variação em texto neutro (sem meta, ADR 012) e a tendência.

**Custo.** As três leituras (operacional, orçamento, diretoria) na ordem. Só entra o
que o modelo calcula: sem previsto por categoria e sem histórico de meses, que o
Portal ainda não tem. A cor da composição do gasto deixou de ser a cor de atenção.

**Modo telão.** `?telao=1` faz as telas passarem sozinhas a cada 20 s, por
`<meta http-equiv="refresh">`: Indicadores (em páginas de 12 cartões) → Saúde →
Custo → volta. Sem JavaScript, e o modo só liga com o parâmetro. É um modo de
exibição, não tela nova, filtro nem exportação, então não contradiz a ADR 005. No
telão cada tela cabe em 1920×1080 sem rolagem: a Saúde passa a três colunas compactas acima de
26 fontes (hml tem 41: ONS 19, CCEE 17, ANEEL 1, BCB 2, IBGE 1, TempoOK 1), os Indicadores paginam e o Custo mostra o topo de cada lista.

**Cache das leituras.** O telão recarrega a cada 20 s, e cada recarga consultava o BigQuery.
Medido em hml em 02/10: cada consulta do Portal varre menos de 1 MiB, mas o BigQuery cobra no
mínimo 10 MiB por consulta e cada uma leva de 1 a 3 s; uma volta do rodízio são cerca de
30 MiB faturados e, deixado ligado o mês inteiro, passa de 1 TiB. O Portal passa a guardar
cada leitura por 300 s (`PORTAL_CACHE_SEGUNDOS`; `0` desliga). As views mudam por lote de
ingestão, então cinco minutos não escondem nada. Erro não é guardado, e o carimbo
"consultado às" mostra a hora em que o dado foi lido de verdade, não a da página.

**Casca comum.** Faixa de topo, navegação e carimbo iguais nas quatro rotas
(`src/portal/pagina.py`). O carimbo diz "consultado às HH:MM (Brasília)": o Portal sabe
quando consultou, não quando o dado chegou.

## 3. Consequências

- **Política de segurança intacta** (`img-src 'none'`, sem script). Os ícones são
  `<svg>` inline e o logo é um caminho vetorial, não uma imagem. A folha de estilo
  está em `src/portal/estilo.py`.
- **Logo.** O arquivo disponível é um PNG de 210×62 px; o caminho foi vetorizado dele
  (`src/portal/marca.py`). Quando a Alup enviar o vetor oficial, troca-se só o
  caminho.
- **Duas decisões de negócio ficam como estavam**: a anomalia de custo é consulta
  com custo mais que o dobro da própria média, e o atraso é o limite de silêncio do
  alerta. Mudar qualquer uma é decisão separada.
- **Limite do telão na Saúde:** um grupo com mais de ~22 fontes deixa de caber em uma
  coluna e o fim dele é cortado. Hoje o maior (ONS) tem 19. Se passar, a saída é paginar
  a Saúde por grupo, como os Indicadores.
- **Não verificado** no navegador real: o layout em celular (o navegador sem cabeça
  não renderiza abaixo de ~500 px) e o texto exato do erro de Secret Manager em
  `hml`, de que depende a regex de `aguardando_credencial`. Se a fonte da Onda 2
  aparecer como crítica e não como "aguardando credencial", o ajuste é nessa regex.
