"""Conector CCEE — CVU merchant por empreendimento (Aditivo 01, público). Item 20.

Fonte: dados abertos da CCEE (CKAN), dataset `custo_variavel_unitario_merchant`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/custo_variavel_unitario_merchant

O CVU de usinas térmicas que vendem no mercado livre (merchant), com e sem a
parcela de recuperação de custo fixo. Uma linha por mês e por modelo de preço
(`CODIGO_MODELO_PRECO`), delimitado por vírgula — como o CVU estrutural.

Perfilado contra a API real em 28/09/2026 (`custo_variavel_unitario_merchant_2026`,
153 linhas): `CVU_CF` vem com `"-"` em 32 linhas (não vazio), quando o modelo
não calcula a parcela de custo fixo — tratado como nulo, igual a vazio.
`RECUPERACAO_CUSTO_FIXO` só trouxe `"Não"` na amostra; o validador aceita
"Sim"/"Não" e rejeita qualquer outro texto, para não inventar um terceiro
valor que a origem não mostrou.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar


class CvuMerchant(BaseModel):
    """O CVU merchant de um empreendimento térmico no mês, em R$/MWh."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    codigo_modelo_preco: str
    empreendimento: str
    despacho: str
    tipo_combustivel: str
    cvu_sem_custo_fixo: Decimal
    cvu_com_custo_fixo: Decimal | None = None
    recupera_custo_fixo: bool
    inicio_suprimento: date
    termino_suprimento: date
    origem_cotacao: str
    periodo_cotacao: str

    @field_validator("codigo_modelo_preco", "empreendimento", "despacho", "tipo_combustivel", "origem_cotacao")
    @classmethod
    def _preenchido(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("campo obrigatório vazio")
        return texto

    @field_validator("cvu_sem_custo_fixo", "cvu_com_custo_fixo")
    @classmethod
    def _nao_negativo(cls, valor: Decimal | None) -> Decimal | None:
        if valor is not None and valor < 0:
            raise ValueError(f"CVU negativo: {valor}")
        return valor

    @field_validator("recupera_custo_fixo", mode="before")
    @classmethod
    def _sim_nao(cls, valor: Any) -> bool:
        texto = limpar(valor).lower() if isinstance(valor, str) else valor
        if texto == "sim":
            return True
        if texto in ("não", "nao"):
            return False
        raise ValueError(f"RECUPERACAO_CUSTO_FIXO inesperado: {valor!r}")

    @field_validator("inicio_suprimento", "termino_suprimento", mode="before")
    @classmethod
    def _parseia_data_br(cls, valor: Any) -> Any:
        """`dd/mm/aaaa` cru → `date`. Ver `CvuEstrutural._parseia_data_br` (mesma regra)."""
        if isinstance(valor, str):
            texto = limpar(valor)
            if not texto:
                raise ValueError("data obrigatória vazia")
            return datetime.strptime(texto, "%d/%m/%Y").date()
        return valor

    @field_validator("periodo_cotacao", mode="before")
    @classmethod
    def _periodo_cotacao(cls, valor: Any) -> Any:
        """`MES_REFERENCIA_COTACAO` não é filtrado pela janela (só `MES_REFERENCIA` é):
        conversão aqui, não em `transformar()`, para um valor malformado descartar
        só esta linha (`ValidationError`), não a execução inteira."""
        if isinstance(valor, str) and len(limpar(valor)) == 6 and limpar(valor).isdigit():
            return periodo_ccee(valor)
        raise ValueError(f"MES_REFERENCIA_COTACAO inválido: {valor!r}")


@registrar
class CceeCvuMerchant(CceeCsvCkan):
    """CVU merchant por empreendimento térmico. CSV por ano, delimitado por vírgula."""

    dataset = "custo_variavel_unitario_merchant"
    entidade = "cvu_merchant"
    schema = CvuMerchant
    delimitador = ","

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        cvu_cf = numero_ou_nulo(bruto.get("CVU_CF"))
        return {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "codigo_modelo_preco": limpar(bruto.get("CODIGO_MODELO_PRECO")),
            "empreendimento": limpar(bruto.get("EMPREENDIMENTO")),
            "despacho": limpar(bruto.get("DESPACHO")),
            "tipo_combustivel": limpar(bruto.get("TIPO_COMBUSTIVEL")),
            "cvu_sem_custo_fixo": numero_ou_nulo(bruto.get("CVU_SCF")),
            "cvu_com_custo_fixo": None if cvu_cf == "-" else cvu_cf,
            "recupera_custo_fixo": bruto.get("RECUPERACAO_CUSTO_FIXO"),
            "inicio_suprimento": bruto.get("DATA_INICIO"),
            "termino_suprimento": bruto.get("DATA_FIM"),
            "origem_cotacao": limpar(bruto.get("ORIGEM_DA_COTACAO")),
            "periodo_cotacao": bruto.get("MES_REFERENCIA_COTACAO"),
        }
