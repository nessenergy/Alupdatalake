"""Conector CCEE — geração horária por parcela de usina (Onda 1, público). Ordem 3 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `geracao_horaria_usina`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/geracao_horaria_usina

A maior fonte do lake: ~3 milhões de linhas por mês (3.984 parcelas de usina ×
744 horas), publicadas **por mês e em gzip** — 61 MB comprimidos, ~800 MB de
texto. É a granularidade de usina que o A7 fixa para dado de portfólio.

Três coisas herdadas do PLD e uma diferença:

- `PERIODO_COMERCIALIZACAO` é o índice da hora **no mês** (1..744), e a hora do
  dia sai da mesma aritmética de `ccee_pld._data_e_hora`;
- o submercado vem por extenso e vira a sigla do ONS;
- o recurso é descoberto no CKAN;
- a diferença: aqui **há** coluna `DATA`. O conector deriva o dia do período,
  compara com a `DATA` publicada, e rejeita a linha se discordarem — é a
  origem mudando a regra, e não cabe a nós escolher qual das duas vale.

`CODIGO_PARCELA_USINA` é código interno da CCEE, não o CEG da ANEEL:
`codigo_usina` fica nulo até o de-para da Lacuna 1 (#141).

`PERIODO_COMERCIALIZACAO` e `DATA` são texto vindo direto do CSV — nem sempre
um número válido nem sempre `dd/mm/aaaa`. Por isso `transformar()` só repassa
essas duas colunas como string; quem converte e deriva é o schema
(`Field(ge=1, le=744)` no período, um `field_validator` no `strptime` da
`DATA`, e um `model_validator` que chama `ccee_pld._data_e_hora` e compara).
Um `ValueError` levantado ali dentro vira `ValidationError` — que é o único
tipo que o runner (`Conector._validar_e_carregar`) captura por linha. Se
`transformar()` levantasse o `ValueError` direto (como uma versão anterior
deste conector fazia), a exceção escaparia do `try/except ValidationError` e
derrubaria as ~3 milhões de linhas do mês inteiro por causa de uma linha.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee
from src.conectores.ccee_pld import SIGLA_SUBMERCADO, SUBMERCADOS, _data_e_hora
from src.core.registry import registrar

TIPOS_USINA = ("Hidráulicas MRE", "Hidráulicas não MRE", "Usinas com CVU", "Biomassa", "Eólicas", "Demais usinas")

# Coluna da origem → coluna do lake. As três primeiras são obrigatórias; as
# outras 25 são nulas na maior parte das linhas (só hidráulicas MRE e usinas
# com CVU as preenchem) e entram como NUMERIC nulo.
MEDIDAS_OBRIGATORIAS = {
    "GERACAO_CENTRO_GRAVIDADE": "geracao_centro_gravidade",
    "FATOR_PERDA_INTERNA": "fator_perda_interna",
    "FATOR_RATEIO_PERDA_GERACAO": "fator_rateio_perda_geracao",
}
MEDIDAS_OPCIONAIS = {
    "GERACAO_SEGURANCA_ENERGETICA": "geracao_seguranca_energetica",
    "GERACAO_RESTRICAO_OPERATIVA_CONST_ON": "geracao_restricao_operativa_constrained_on",
    "ENERGIA_AJUSTADA_ENCARGO_RESTRICAO_OPERATIVA": "energia_ajustada_encargo_restricao_operativa",
    "INDISPONIBILIDADE_UTE_ORDEM_MERITO_ECONOMICO": "indisponibilidade_ute_ordem_merito",
    "CUSTO_DECLARADO_PARCELA_USINA": "custo_declarado_parcela_usina",
    "FATOR_DESLOCAMENTO_HIDRAULICO": "fator_deslocamento_hidraulico",
    "GERACAO_VERIFICADA_ONS": "geracao_verificada_ons",
    "DISPONIBILIDADE_VERIFICADA_UG": "disponibilidade_verificada_ug",
    "GERACAO_INFLEXIVEL": "geracao_inflexivel",
    "GERACAO_SUBSTITUTA_COMPENSACAO_INDISPONIBILIDADE": "geracao_substituta_compensacao_indisponibilidade",
    "DESPACHO_RESTRICAO_ENERGETICA_EX_ANTE": "despacho_restricao_energetica_ex_ante",
    "DESPACHO_PAGAMENTO_ENCARGO_RESTRICAO_OPERACAO": "despacho_pagamento_encargo_restricao_operacao",
    "GERACAO_FORA_ORDEM_MERITO": "geracao_fora_ordem_merito",
    "DESPACHO_ORDEM_MERITO_DECK_ONS": "despacho_ordem_merito_deck_ons",
    "DESPACHO_ORDEM_MERITO_PRECO": "despacho_ordem_merito_preco",
    "DESPACHO_ORDEM_MERITO": "despacho_ordem_merito",
    "GERACAO_RESERVA_POTENCIA": "geracao_reserva_potencia",
    "PRECO_ENCARGO_RESERVA_POTENCIA": "preco_encargo_reserva_potencia",
    "GERACAO_UNIT_COMMITMENT": "geracao_unit_commitment",
    "GERACAO_FINAL_ORDEM_MERITO": "geracao_final_ordem_merito",
    "DESLOCAMENTO_HIDRAULICO_ENERGETICO_PRELIMINAR": "deslocamento_hidraulico_energetico_preliminar",
    "GARANTIA_FISICA_AJUSTADA_FATOR_DISPONIBILIDADE": "garantia_fisica_ajustada_fator_disponibilidade",
    "GARANTIA_FISICA_RRH_MODULADA_AJUSTADA_2": "garantia_fisica_rrh_modulada_ajustada_2",
    "GARANTIA_FISICA_RRH_MODULADA_AJUSTADA_3": "garantia_fisica_rrh_modulada_ajustada_3",
    "FATOR_RISCO_HIDROLOGICO": "fator_risco_hidrologico",
}


class GeracaoHorariaUsina(BaseModel):
    """A geração de uma parcela de usina em uma hora do mês de apuração.

    `data_referencia` e `hora` não vêm prontos: são derivados de
    `mes_referencia` + `periodo_comercializacao` pelo `model_validator` no fim
    da classe, com a mesma aritmética de `ccee_pld._data_e_hora`.
    """

    mes_referencia: str = Field(exclude=True)  # AAAAMM cru — só deriva data_referencia/hora; não é coluna do lake
    data_referencia: date | None = None  # preenchido por `_deriva_data_e_hora_e_confere_periodo`
    data_publicada: date  # a DATA que a CCEE escreve, já parseada; tem de bater com a derivada do período
    hora: int | None = None  # idem data_referencia
    periodo_comercializacao: int = Field(ge=1, le=744)
    periodo_apuracao_ccee: str
    versao_publicacao: date
    codigo_parcela_usina: str
    sigla_usina: str
    fonte_primaria: str
    submercado: str
    tipo_usina: Literal[TIPOS_USINA]  # type: ignore[valid-type]
    geracao_centro_gravidade: Decimal
    fator_perda_interna: Decimal
    fator_rateio_perda_geracao: Decimal
    geracao_seguranca_energetica: Decimal | None = None
    geracao_restricao_operativa_constrained_on: Decimal | None = None
    energia_ajustada_encargo_restricao_operativa: Decimal | None = None
    indisponibilidade_ute_ordem_merito: Decimal | None = None
    custo_declarado_parcela_usina: Decimal | None = None
    fator_deslocamento_hidraulico: Decimal | None = None
    geracao_verificada_ons: Decimal | None = None
    disponibilidade_verificada_ug: Decimal | None = None
    geracao_inflexivel: Decimal | None = None
    geracao_substituta_compensacao_indisponibilidade: Decimal | None = None
    despacho_restricao_energetica_ex_ante: Decimal | None = None
    despacho_pagamento_encargo_restricao_operacao: Decimal | None = None
    geracao_fora_ordem_merito: Decimal | None = None
    despacho_ordem_merito_deck_ons: Decimal | None = None
    despacho_ordem_merito_preco: Decimal | None = None
    despacho_ordem_merito: Decimal | None = None
    geracao_reserva_potencia: Decimal | None = None
    preco_encargo_reserva_potencia: Decimal | None = None
    geracao_unit_commitment: Decimal | None = None
    geracao_final_ordem_merito: Decimal | None = None
    deslocamento_hidraulico_energetico_preliminar: Decimal | None = None
    garantia_fisica_ajustada_fator_disponibilidade: Decimal | None = None
    garantia_fisica_rrh_modulada_ajustada_2: Decimal | None = None
    garantia_fisica_rrh_modulada_ajustada_3: Decimal | None = None
    fator_risco_hidrologico: Decimal | None = None

    @field_validator("data_publicada", mode="before")
    @classmethod
    def _parseia_data_publicada(cls, valor: Any) -> Any:
        """`dd/mm/aaaa` cru → `date`. Formato que não bate vira `ValidationError`
        (linha inválida, não crash) — o `ValueError` do `strptime` é capturado
        pelo próprio pydantic, aqui dentro do validador."""
        if isinstance(valor, str):
            return datetime.strptime(valor, "%d/%m/%Y").date()
        return valor

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        if valor not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return valor

    @model_validator(mode="after")
    def _deriva_data_e_hora_e_confere_periodo(self) -> GeracaoHorariaUsina:
        """Deriva `data_referencia`/`hora` de `mes_referencia` + `periodo_comercializacao`
        (mesma aritmética de `ccee_pld._data_e_hora`, que também rejeita período
        fora do mês) e confere com a `DATA` publicada; se discordarem, a origem
        mudou a regra. As duas coisas viram `ValueError` — e, por rodar dentro
        de um `model_validator`, o pydantic converte em `ValidationError`:
        linha inválida, contada, sem derrubar o mês inteiro."""
        dia, hora = _data_e_hora(self.mes_referencia, self.periodo_comercializacao)
        if self.data_publicada != dia:
            raise ValueError(
                f"DATA {self.data_publicada} não bate com o período {self.periodo_comercializacao} ({dia})"
            )
        self.data_referencia = dia
        self.hora = hora
        return self


@registrar
class CceeGeracaoUsina(CceeCsvCkan):
    """Geração horária por parcela de usina. Gzip por mês; ~3 milhões de linhas cada."""

    dataset = "geracao_horaria_usina"
    entidade = "geracao_usina"
    schema = GeracaoHorariaUsina
    recurso_por = "mes"

    # Medido em 24/09 com o teto default de 8 MiB: lote fechava a cada ~5.900
    # linhas (~5s por load job), e o mês (~3M linhas) não cabia no timeout do
    # job. 32 MiB dá 4x menos load jobs. O pico de memória medido com 8 MiB foi
    # 225 MiB; com 32 MiB o pico estimado segue dentro do 1 GiB do job, mas o
    # payload que o `load_table_from_json` monta cresce com o lote — não
    # remedido ainda, a confirmar na primeira carga real com 32 MiB.
    bytes_por_lote = 32 * 1024 * 1024

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        # `transformar()` só repassa texto: MES_REFERENCIA já chegou validado
        # (a base descarta linha com mês malformado antes de render aqui — ver
        # `CceeCsvCkan._dentro`), mas PERIODO_COMERCIALIZACAO e DATA, não — quem
        # converte e pode rejeitar essas duas é o schema, não este método (veja
        # o docstring do módulo).
        mes = limpar(bruto["MES_REFERENCIA"])
        nome = limpar(bruto.get("SUBMERCADO")).upper()

        registro: dict[str, Any] = {
            "mes_referencia": mes,
            "periodo_comercializacao": limpar(bruto.get("PERIODO_COMERCIALIZACAO")),
            "data_publicada": limpar(bruto.get("DATA")),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "codigo_parcela_usina": limpar(bruto.get("CODIGO_PARCELA_USINA")),
            "sigla_usina": limpar(bruto.get("SIGLA_USINA")),
            "fonte_primaria": limpar(bruto.get("FONTE_PRIMARIA")),
            "submercado": SIGLA_SUBMERCADO.get(nome, nome),
            "tipo_usina": limpar(bruto.get("TIPO_USINA")),
        }
        for origem, destino in MEDIDAS_OBRIGATORIAS.items():
            registro[destino] = numero_ou_nulo(bruto.get(origem))  # None → o schema rejeita
        for origem, destino in MEDIDAS_OPCIONAIS.items():
            registro[destino] = numero_ou_nulo(bruto.get(origem))
        return registro
