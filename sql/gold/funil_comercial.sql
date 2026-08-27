-- Gold: quanto está parado em cada estágio do funil, e há quanto tempo.
-- Responde "onde o pipeline comercial está travado", não "quais negócios existem".
CREATE OR REPLACE VIEW `${projeto}.${gold}.funil_comercial` AS
SELECT
  pipeline,
  estagio,
  COUNT(*)                                        AS negocios,
  SUM(valor)                                      AS valor_total,
  AVG(valor)                                      AS valor_medio,
  AVG(DATE_DIFF(CURRENT_DATE(), DATE(criado_em), DAY))      AS idade_media_dias,
  MIN(data_fechamento)                            AS fechamento_mais_proximo,
  COUNTIF(data_fechamento < CURRENT_DATE())       AS negocios_com_fechamento_vencido
FROM `${projeto}.${silver}.hubspot_negocios`
GROUP BY pipeline, estagio;
