"""Conector CCEE — resultado da contabilização por perfil de agente (Onda 1, público). Ordem 2 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `contabilizacao_montante_perfil_agente`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/contabilizacao_montante_perfil_agente

Uma linha por perfil de agente e mês, com os 16 componentes do resultado
financeiro no MCP e o `RESULTADO_FINAL`. ~47.000 perfis por mês.

**É a fonte que aceita a ADR 016.** A recontabilização está no dado
(`AJUSTE_RECONTAB`) e a CCEE reescreve o recurso do ano inteiro ao republicar.
O identificador de versão é o `last_modified` do recurso no CKAN, que a base
`CceeCsvCkan` injeta como `_versao_publicacao`. A Silver vigente ordena por
ele; a Silver `_historico` guarda uma linha por chave e versão.

O arquivo traz `COD_AGENTE`, não a sigla do agente: `agente_ccee` fica nulo na
Silver, e a Gold traz a sigla juntando com `gold.agentes_ccee` por
`codigo_perfil`.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar

# Coluna da origem → coluna do lake, na ordem do arquivo. Todos em R$.
VALORES = {
    "VALOR_TM_MCP": "valor_tm_mcp",
    "COMPENSACAO_MRE": "compensacao_mre",
    "VALOR_ENCARGO": "valor_encargo",
    "VALOR_AJUSTE_EXPOSICAO": "valor_ajuste_exposicao",
    "VALOR_AJUSTE_ALIVIO_RET": "valor_ajuste_alivio_retroativo",
    "EFEITO_CONTRAT_DISP": "efeito_contratos_disponibilidade",
    "EFEITO_CONTRAT_COTA_GF": "efeito_contratos_cota_gf",
    "EFEITO_CONTRAT_NUCLEAR": "efeito_contratos_nuclear",
    "AJUSTE_RECONTAB": "ajuste_recontab",
    "AJUSTE_MCSD_EX": "ajuste_mcsd_ex",
    "RESULTADO_FINANCEIRO_ER": "resultado_financeiro_energia_reserva",
    "EFEITO_CCEARQ": "efeito_ccearq",
    "EFEITO_CONTRAT_ITAIPU": "efeito_contratos_itaipu",
    "EFEITO_REPASSE_RISCO_HIDRO": "efeito_repasse_risco_hidrologico",
    "EFEITO_DESLOC_PLD_CMO": "efeito_deslocamento_pld_cmo",
    "RESULTADO_FINAL": "resultado_final",
}


class ContabilizacaoPerfil(BaseModel):
    """O resultado financeiro de um perfil de agente em um mês de apuração."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    codigo_agente: str
    codigo_perfil: str
    sigla_perfil: str
    nome_empresarial: str
    cnpj: str
    valor_tm_mcp: Decimal | None = None
    compensacao_mre: Decimal | None = None
    valor_encargo: Decimal | None = None
    valor_ajuste_exposicao: Decimal | None = None
    valor_ajuste_alivio_retroativo: Decimal | None = None
    efeito_contratos_disponibilidade: Decimal | None = None
    efeito_contratos_cota_gf: Decimal | None = None
    efeito_contratos_nuclear: Decimal | None = None
    ajuste_recontab: Decimal | None = None
    ajuste_mcsd_ex: Decimal | None = None
    resultado_financeiro_energia_reserva: Decimal | None = None
    efeito_ccearq: Decimal | None = None
    efeito_contratos_itaipu: Decimal | None = None
    efeito_repasse_risco_hidrologico: Decimal | None = None
    efeito_deslocamento_pld_cmo: Decimal | None = None
    resultado_final: Decimal | None = None

    @field_validator("cnpj")
    @classmethod
    def _cnpj_normalizado(cls, valor: str) -> str:
        digitos = "".join(c for c in valor if c.isdigit())
        if len(digitos) != 14:
            raise ValueError(f"CNPJ deve ter 14 dígitos, veio com {len(digitos)}")
        return digitos

    @field_validator("codigo_agente", "codigo_perfil")
    @classmethod
    def _codigo_numerico(cls, valor: str) -> str:
        codigo = valor.strip()
        if not codigo.isdigit():
            raise ValueError(f"código deve ser numérico: {valor!r}")
        return codigo


@registrar
class CceeContabilizacaoPerfil(CceeCsvCkan):
    """Contabilização por perfil. CSV por ano, uma linha por perfil e mês."""

    dataset = "contabilizacao_montante_perfil_agente"
    entidade = "contabilizacao_perfil"
    schema = ContabilizacaoPerfil

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        registro: dict[str, Any] = {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "codigo_agente": limpar(bruto.get("COD_AGENTE")),
            "codigo_perfil": limpar(bruto.get("COD_PERF_AGENTE")),
            "sigla_perfil": limpar(bruto.get("SIGLA_PERFIL_AGENTE")),
            "nome_empresarial": limpar(bruto.get("NOME_EMPRESARIAL")),
            "cnpj": limpar(bruto.get("CNPJ")),
        }
        for origem, destino in VALORES.items():
            registro[destino] = numero_ou_nulo(bruto.get(origem))
        return registro
