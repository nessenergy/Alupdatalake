-- Gold: retrato do parque gerador por UF e fonte — quanto de potência existe,
-- quanto está em operação e quanto ainda está em construção.
CREATE OR REPLACE VIEW `${projeto}.${gold}.parque_gerador` AS
SELECT
  uf,
  tipo_geracao,
  origem_combustivel,
  COUNT(*)                                                              AS usinas,
  SUM(potencia_fiscalizada_kw) / 1000                                   AS potencia_fiscalizada_mw,
  SUM(IF(fase = 'Operação', potencia_fiscalizada_kw, 0)) / 1000         AS potencia_em_operacao_mw,
  SUM(IF(fase != 'Operação', COALESCE(potencia_outorgada_kw, 0), 0)) / 1000 AS potencia_em_expansao_mw,
  SUM(garantia_fisica_kw) / 1000                                        AS garantia_fisica_mw
FROM `${projeto}.${silver}.aneel_siga`
GROUP BY uf, tipo_geracao, origem_combustivel;
