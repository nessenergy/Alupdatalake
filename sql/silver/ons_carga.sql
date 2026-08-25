-- Silver: carga diária higienizada e deduplicada.
-- Dedup por (data_referencia, submercado): o ONS revisa dado publicado, então
-- vence a ingestão mais recente.
CREATE OR REPLACE VIEW `${projeto}.${silver}.ons_carga` AS
SELECT
  data_referencia,
  submercado,
  CAST(NULL AS STRING) AS codigo_usina,  -- carga é agregada por subsistema
  CAST(NULL AS STRING) AS agente_ccee,   -- idem
  FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,
  nome_subsistema,
  carga_mwmed,
  _ingestao_id,
  _ingestao_timestamp
FROM `${projeto}.${bronze}.ons_carga`
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY data_referencia, submercado
  ORDER BY _ingestao_timestamp DESC
) = 1;
