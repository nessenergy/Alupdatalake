-- Silver: IPCA higienizado e deduplicado, com as dimensões comuns.
-- Dedup: para cada (data_referencia, variavel_id), vence a ingestão mais recente.
-- O IBGE revisa série publicada, então a última ingestão é a versão correta.
CREATE OR REPLACE VIEW `${projeto}.${silver}.ibge_ipca` AS
SELECT
  data_referencia,
  CAST(NULL AS STRING) AS submercado,     -- índice nacional, não é dado de submercado
  CAST(NULL AS STRING) AS codigo_usina,   -- idem
  CAST(NULL AS STRING) AS agente_ccee,    -- idem
  FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,
  variavel_id,
  variavel,
  unidade,
  valor,
  _ingestao_id,
  _ingestao_timestamp
FROM `${projeto}.${bronze}.ibge_ipca`
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY data_referencia, variavel_id
  ORDER BY _ingestao_timestamp DESC
) = 1;
