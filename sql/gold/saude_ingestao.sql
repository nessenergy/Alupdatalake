-- Gold: saúde da ingestão, uma linha por fonte.
-- Responde "o dado está fresco, e dá para confiar nele?" — é a view que o
-- painel de monitoramento consome. Não é relatório de negócio: a matéria-prima
-- é o log de execução, não o dado ingerido.
--
-- O intervalo esperado entre execuções é **inferido do próprio histórico**
-- (mediana dos intervalos observados), não declarado. Declarar significaria
-- repetir o cron do Terraform aqui, e as duas cópias divergiriam na primeira
-- vez que alguém mudasse o agendamento sem lembrar desta view.
CREATE OR REPLACE VIEW `${projeto}.${gold}.saude_ingestao` AS
WITH execucoes AS (
  SELECT
    CONCAT(fonte, '_', entidade) AS conector,
    status,
    linhas_extraidas,
    linhas_invalidas,
    linhas_carregadas,
    encerrada_em,
    duracao_segundos,
    erro
  FROM `${projeto}.${bronze}._execucoes`
  WHERE encerrada_em IS NOT NULL
),
intervalos AS (
  SELECT
    conector,
    TIMESTAMP_DIFF(
      encerrada_em,
      LAG(encerrada_em) OVER (PARTITION BY conector ORDER BY encerrada_em),
      MINUTE
    ) AS minutos_desde_anterior
  FROM execucoes
  WHERE status = 'SUCESSO'
),
cadencia AS (
  SELECT
    conector,
    APPROX_QUANTILES(minutos_desde_anterior, 2)[OFFSET(1)] AS intervalo_tipico_min
  FROM intervalos
  WHERE minutos_desde_anterior IS NOT NULL
  GROUP BY conector
),
agregado AS (
  SELECT
    conector,
    MAX(IF(status = 'SUCESSO', encerrada_em, NULL)) AS ultimo_sucesso,
    MAX(encerrada_em)                               AS ultima_execucao,
    COUNTIF(encerrada_em >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)) AS execucoes_30d,
    COUNTIF(status = 'SUCESSO' AND encerrada_em >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY))
      AS sucessos_30d,
    SUM(linhas_carregadas)                          AS linhas_carregadas_total,
    SAFE_DIVIDE(SUM(linhas_invalidas), NULLIF(SUM(linhas_extraidas), 0)) AS taxa_invalidas,
    APPROX_QUANTILES(duracao_segundos, 100)[OFFSET(50)] AS duracao_p50_seg,
    APPROX_QUANTILES(duracao_segundos, 100)[OFFSET(95)] AS duracao_p95_seg,
    MAX(IF(status = 'ERRO', erro, NULL))            AS ultimo_erro
  FROM execucoes
  GROUP BY conector
)
SELECT
  a.conector,
  a.ultimo_sucesso,
  a.ultima_execucao,
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), a.ultimo_sucesso, MINUTE) AS minutos_desde_sucesso,
  c.intervalo_tipico_min,
  a.execucoes_30d,
  SAFE_DIVIDE(a.sucessos_30d, NULLIF(a.execucoes_30d, 0)) AS taxa_sucesso_30d,
  a.taxa_invalidas,
  a.linhas_carregadas_total,
  a.duracao_p50_seg,
  a.duracao_p95_seg,
  a.ultimo_erro,
  -- Semáforo. Atraso é medido contra a cadência da própria fonte: o dobro do
  -- intervalo típico. Sem histórico suficiente, cai para 26h — um dia mais a
  -- folga de um atraso de publicação.
  CASE
    WHEN a.ultimo_sucesso IS NULL THEN 'SEM_SUCESSO'
    WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), a.ultimo_sucesso, MINUTE)
         > 2 * COALESCE(c.intervalo_tipico_min, 1560) THEN 'ATRASADA'
    WHEN a.ultima_execucao > a.ultimo_sucesso THEN 'FALHA_RECENTE'
    ELSE 'OK'
  END AS situacao
FROM agregado a
LEFT JOIN cadencia c USING (conector);
