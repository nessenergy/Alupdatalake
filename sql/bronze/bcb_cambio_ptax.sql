-- Bronze: cotação PTAX do dólar (BCB/Olinda).
-- Append-only: reprocessar a mesma janela insere de novo; a Silver deduplica.
CREATE TABLE IF NOT EXISTS `${projeto}.${bronze}.bcb_cambio_ptax` (
  data_referencia     DATE      NOT NULL OPTIONS(description="Data do boletim"),
  data_hora_cotacao   TIMESTAMP NOT NULL OPTIONS(description="Instante da cotação, conforme o BCB"),
  tipo_boletim        STRING    NOT NULL OPTIONS(description="Abertura, Intermediário, Fechamento"),
  cotacao_compra      NUMERIC   NOT NULL OPTIONS(description="BRL por USD, ponta de compra"),
  cotacao_venda       NUMERIC   NOT NULL OPTIONS(description="BRL por USD, ponta de venda"),

  _ingestao_id        STRING    NOT NULL OPTIONS(description="Identificador da execução de ingestão"),
  _ingestao_timestamp TIMESTAMP NOT NULL OPTIONS(description="Quando o registro entrou no lake"),
  _fonte              STRING    NOT NULL OPTIONS(description="Identificador da fonte"),
  _schema_versao      STRING    NOT NULL OPTIONS(description="Versão do contrato lido na origem")
)
PARTITION BY DATE(_ingestao_timestamp)
CLUSTER BY data_referencia
OPTIONS(description="Cotações PTAX do dólar — camada Bronze, append-only");
