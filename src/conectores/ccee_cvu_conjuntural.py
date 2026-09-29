"""Conector CCEE — CVU conjuntural por agente vendedor (Aditivo 01, público). Item 21.

Fonte: dados abertos da CCEE (CKAN), dataset `custo_variavel_unitario_conjuntural`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/custo_variavel_unitario_conjuntural

O CVU conjuntural (calculado a partir do custo real de combustível do mês,
diferente do CVU estrutural, fixado por leilão) por agente vendedor, leilão e
produto. Mesma forma do CVU conjuntural revisado (`ccee_cvu_conjuntural_revisado`):
o schema e a transformação vivem aqui e são reaproveitados lá.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar


class CvuConjuntural(BaseModel):
    """O CVU conjuntural de um agente vendedor no mês, em R$/MWh."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    agente_vendedor: str
    cnpj_agente_vendedor: str
    sigla_parcela: str
    tipo_combustivel: str
    leilao: str
    produto: str
    custo_combustivel: Decimal
    cvu_conjuntural: Decimal
    codigo_modelo_preco: str
    inicio_suprimento: date
    termino_suprimento: date

    @field_validator("agente_vendedor", "sigla_parcela", "tipo_combustivel", "leilao", "produto", "codigo_modelo_preco")
    @classmethod
    def _preenchido(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("campo obrigatório vazio")
        return texto

    @field_validator("cnpj_agente_vendedor")
    @classmethod
    def _cnpj_normalizado(cls, valor: str) -> str:
        # O arquivo de 2025 perdeu o zero à esquerda (13 dígitos, planilha).
        digitos = "".join(c for c in valor if c.isdigit()).zfill(14)
        if len(digitos) != 14:
            raise ValueError(f"CNPJ deve ter 14 dígitos, veio com {len(digitos)}")
        return digitos

    @field_validator("custo_combustivel", "cvu_conjuntural")
    @classmethod
    def _nao_negativo(cls, valor: Decimal) -> Decimal:
        if valor < 0:
            raise ValueError(f"valor negativo: {valor}")
        return valor

    @field_validator("inicio_suprimento", "termino_suprimento", mode="before")
    @classmethod
    def _parseia_data_br(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            texto = limpar(valor)
            if not texto:
                raise ValueError("data obrigatória vazia")
            return datetime.strptime(texto, "%d/%m/%Y").date()
        return valor


def transformar_cvu_conjuntural(bruto: dict[str, Any]) -> dict[str, Any]:
    """Reaproveitado por `ccee_cvu_conjuntural_revisado`: os dois datasets têm o mesmo layout."""
    mes = bruto["MES_REFERENCIA"]
    return {
        "data_referencia": primeiro_dia(mes),
        "periodo_apuracao_ccee": periodo_ccee(mes),
        "versao_publicacao": bruto["_versao_publicacao"],
        "agente_vendedor": limpar(bruto.get("AGENTE_VENDEDOR")),
        "cnpj_agente_vendedor": limpar(bruto.get("CNPJ_AGENTE_VENDEDOR")),
        "sigla_parcela": limpar(bruto.get("SIGLA_PARCELA")),
        "tipo_combustivel": limpar(bruto.get("TIPO_COMBUSTIVEL")),
        "leilao": limpar(bruto.get("LEILAO")),
        "produto": limpar(bruto.get("PRODUTO")),
        "custo_combustivel": numero_ou_nulo(bruto.get("CUSTO_COMBUSTIVEL")),
        "cvu_conjuntural": numero_ou_nulo(bruto.get("CVU_CONJUNTURAL")),
        # 2025 publica o cabeçalho com cedilha (`CODIGO_MODELO_PREÇO`); 2026, sem.
        "codigo_modelo_preco": limpar(bruto.get("CODIGO_MODELO_PRECO") or bruto.get("CODIGO_MODELO_PREÇO")),
        "inicio_suprimento": bruto.get("INICIO_SUPRIMENTO"),
        "termino_suprimento": bruto.get("TERMINO_SUPRIMENTO"),
    }


@registrar
class CceeCvuConjuntural(CceeCsvCkan):
    """CVU conjuntural por agente vendedor. CSV por ano, delimitado por vírgula."""

    dataset = "custo_variavel_unitario_conjuntural"
    entidade = "cvu_conjuntural"
    schema = CvuConjuntural
    delimitador = ","

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return transformar_cvu_conjuntural(bruto)
