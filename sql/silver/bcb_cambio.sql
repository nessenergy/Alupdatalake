-- Silver: PTAX higienizada, deduplicada e com as dimensões comuns.
-- Dedup: para cada (data_referencia, tipo_boletim), vence a ingestão mais recente.
CREATE OR REPLACE VIEW `${projeto}.${silver}.bcb_cambio` AS
SELECT
  data_referencia,
  CAST(NULL AS STRING)  AS submercado,      -- câmbio não é dado de submercado
  CAST(NULL AS STRING)  AS codigo_usina,    -- idem
  CAST(NULL AS STRING)  AS agente_ccee,     -- idem
  FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,
  tipo_boletim,
  data_hora_cotacao,
  cotacao_compra,
  cotacao_venda,
  (cotacao_compra + cotacao_venda) / 2 AS cotacao_media,
  _ingestao_id,
  _ingestao_timestamp
FROM `${projeto}.${bronze}.bcb_cambio_ptax`
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY data_referencia, tipo_boletim
  ORDER BY _ingestao_timestamp DESC
) = 1;
