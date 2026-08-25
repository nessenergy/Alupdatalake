-- Log operacional de toda ingestão. Responde "o dado de ontem entrou?" sem
-- abrir o orquestrador, e é evidência de homologação de onda.
CREATE TABLE IF NOT EXISTS `${projeto}.${bronze}._execucoes` (
  ingestao_id      STRING    NOT NULL,
  fonte            STRING    NOT NULL,
  entidade         STRING    NOT NULL,
  janela_inicio    DATE      NOT NULL,
  janela_fim       DATE      NOT NULL,
  status           STRING    NOT NULL OPTIONS(description="SUCESSO | ERRO | EM_EXECUCAO"),
  linhas_extraidas INT64,
  linhas_invalidas INT64,
  linhas_carregadas INT64,
  iniciada_em      TIMESTAMP NOT NULL,
  encerrada_em     TIMESTAMP,
  duracao_segundos FLOAT64,
  erro             STRING
)
PARTITION BY DATE(iniciada_em)
CLUSTER BY fonte, status
OPTIONS(description="Controle de execuções de ingestão do AlupData");
