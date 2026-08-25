-- Gold: IPCA por mês em uma linha — insumo de reajuste de contrato e de
-- deflacionamento de série de preço.
CREATE OR REPLACE VIEW `${projeto}.${gold}.inflacao_mensal` AS
SELECT
  periodo_apuracao,
  data_referencia,
  MAX(IF(variavel_id = '63', valor, NULL)) AS ipca_mes,
  MAX(IF(variavel_id = '69', valor, NULL)) AS ipca_acumulado_ano
FROM `${projeto}.${silver}.ibge_ipca`
GROUP BY periodo_apuracao, data_referencia;
