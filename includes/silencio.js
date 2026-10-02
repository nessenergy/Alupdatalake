// Limite de silêncio por conector, em horas: o mesmo de
// `conectores_criticos` em infra/modules/monitoramento/main.tf, que dispara o
// alerta. A Gold `saude_ingestao` marca ATRASADA com este número, então
// "atrasada" no Portal significa o mesmo que alerta disparado.
// tests/unit/test_sql.py confere que as duas listas são iguais.
const limites_horas = {
  bcb_cambio_ptax: 26,
  bcb_juros: 26,
  ons_carga: 26,
  ons_ear: 26,
  ons_ena: 26,
  ons_ear_bacia: 26,
  ons_ena_bacia: 26,
  ons_ear_reservatorio: 26,
  ons_ena_reservatorio: 26,
  ons_intercambio_nacional: 26,
  ons_intercambio_internacional: 26,
  ons_geracao_exportacao: 26,
  ons_balanco_energia: 26,
  ons_cmo_semi_horario: 26,
  ons_carga_programada: 26,
  ons_carga_verificada: 26,
  ons_volume_espera: 26,
  ons_programacao_previsao: 26,
  ons_balanco_dessem: 26,
  ons_cvu_termica: 180,
  aneel_siga: 180,
  ons_capacidade: 180,
  ons_geracao_usina: 780,
  ons_disponibilidade_usina: 780,
  ons_restricao_coff_eolica: 780,
  ons_restricao_coff_fotovoltaica: 780,
  ons_dados_hidrologicos: 780,
  ons_energia_vertida_turbinavel: 780,
  ons_geracao_termica_despacho: 780,
  ons_fator_capacidade: 780,
  ibge_ipca: 780,
  ccee_pld: 26,
  ccee_perfil: 180,
  ccee_agente: 780,
  ccee_exposicao_financeira: 780,
  ccee_contabilizacao_perfil: 780,
  ccee_geracao_usina: 780,
  ccee_contrato_montante: 780,
  ccee_varejista_consumidor: 780,
  ccee_encargo_ess: 780,
  ccee_energia_reserva: 780,
  ccee_cvu_estrutural: 780,
  ccee_cvu_merchant: 780,
  ccee_cvu_conjuntural: 780,
  ccee_cvu_conjuntural_revisado: 780,
  ccee_reserva_encargo: 780,
  ccee_energia_reserva_consumo_referencia: 780,
  ccee_consumo_classe_agente: 780,
};

// Linhas para UNNEST no SQL: STRUCT(conector, limite_h).
function valores() {
  return Object.entries(limites_horas)
    .map(([conector, horas]) => `STRUCT('${conector}' AS conector, ${horas} AS limite_h)`)
    .join(",\n    ");
}

module.exports = { limites_horas, valores };
