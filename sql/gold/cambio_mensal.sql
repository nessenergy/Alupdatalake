-- Gold: câmbio de fechamento por mês — insumo de conversão de contratos
-- indexados em dólar. Usa só o boletim de fechamento.
CREATE OR REPLACE VIEW `${projeto}.${gold}.cambio_mensal` AS
SELECT
  periodo_apuracao,
  MIN(data_referencia) AS primeiro_dia_util,
  MAX(data_referencia) AS ultimo_dia_util,
  COUNT(*)             AS dias_uteis,
  AVG(cotacao_media)   AS cambio_medio,
  MIN(cotacao_media)   AS cambio_minimo,
  MAX(cotacao_media)   AS cambio_maximo,
  ARRAY_AGG(cotacao_media ORDER BY data_referencia DESC LIMIT 1)[OFFSET(0)] AS cambio_fechamento
FROM `${projeto}.${silver}.bcb_cambio_ptax`
WHERE tipo_boletim = 'Fechamento'
GROUP BY periodo_apuracao;
