-- Gold: volumetria diária por conector — quanto dado entrou, e a tendência.
-- Base da projeção de custo de armazenamento e do "isso cresceu do nada?".
CREATE OR REPLACE VIEW `${projeto}.${gold}.volumetria_lake` AS
SELECT
  CONCAT(fonte, '_', entidade)  AS conector,
  DATE(encerrada_em)            AS dia,
  COUNT(*)                      AS execucoes,
  COUNTIF(status = 'ERRO')      AS execucoes_com_erro,
  SUM(linhas_extraidas)         AS linhas_extraidas,
  SUM(linhas_invalidas)         AS linhas_invalidas,
  SUM(linhas_carregadas)        AS linhas_carregadas,
  SUM(duracao_segundos)         AS segundos_totais
FROM `${projeto}.${bronze}._execucoes`
WHERE encerrada_em >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
GROUP BY conector, dia;
