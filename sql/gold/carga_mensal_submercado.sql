-- Gold: carga mensal por submercado — média, pico e vale do mês.
-- Base de comparação entre submercados e de análise sazonal.
CREATE OR REPLACE VIEW `${projeto}.${gold}.carga_mensal_submercado` AS
SELECT
  periodo_apuracao,
  submercado,
  ANY_VALUE(nome_subsistema) AS nome_subsistema,
  COUNT(*)                   AS dias,
  AVG(carga_mwmed)           AS carga_media_mwmed,
  MAX(carga_mwmed)           AS carga_maxima_mwmed,
  MIN(carga_mwmed)           AS carga_minima_mwmed
FROM `${projeto}.${silver}.ons_carga`
GROUP BY periodo_apuracao, submercado;
