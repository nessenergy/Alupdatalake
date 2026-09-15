"""Conector CCEE — custo variável unitário estrutural por usina (Onda 1, público). Ordem 5 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `custo_variavel_unitario_estrutural`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/custo_variavel_unitario_estrutural

O CVU que o B1 nomeia em Mercado de Energia. Uma linha por usina, leilão,
produto e **ano de horizonte** no mês de referência: a mesma usina aparece uma
vez por ano projetado. É o único CSV da CCEE com **vírgula** como delimitador,
e traz datas em `dd/mm/aaaa`.

`CODIGO_PARCELA_USINA` é código interno da CCEE, não CEG: `codigo_usina` fica
nulo até o de-para (#141), como na geração.

Perfilamento contra a API real em 14/09/2026 (`custo_variavel_unitario_estrutural_2026`,
4.715 linhas): a chave candidata do Questionário — (`MES_REFERENCIA`,
`ANO_HORIZONTE`, `CODIGO_PARCELA_USINA`, `LEILAO`, `PRODUTO`) — tinha 185
duplicatas. Com `CODIGO_MODELO_PRECO` acrescentado, zero. Ver
`docs/dicionario-dados/ccee_cvu_estrutural.md` para os números completos.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar


class CvuEstrutural(BaseModel):
    """O CVU estrutural de uma usina para um ano de horizonte, no mês de referência."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    ano_horizonte: int = Field(ge=2000, le=2100)
    codigo_parcela_usina: str | None = None
    sigla_parcela: str
    tipo_combustivel: str
    leilao: str
    produto: str
    cvu_estrutural: Decimal = Field(ge=0, description="R$/MWh")
    codigo_modelo_preco: str
    inicio_suprimento: date | None = None
    termino_suprimento: date | None = None

    @field_validator("inicio_suprimento", "termino_suprimento", mode="before")
    @classmethod
    def _parseia_data_br(cls, valor: Any) -> Any:
        """`dd/mm/aaaa` cru → `date`. Formato que não bate vira `ValidationError`
        (linha inválida, não crash) — o `ValueError` do `strptime` é capturado
        pelo próprio pydantic, aqui dentro do validador: mesma regra da
        geração horária, falha de parse vira `ValidationError`, contada."""
        if isinstance(valor, str):
            texto = limpar(valor)
            return datetime.strptime(texto, "%d/%m/%Y").date() if texto else None
        return valor


@registrar
class CceeCvuEstrutural(CceeCsvCkan):
    """CVU estrutural por usina e horizonte. CSV por ano, delimitado por vírgula."""

    dataset = "custo_variavel_unitario_estrutural"
    entidade = "cvu_estrutural"
    schema = CvuEstrutural
    delimitador = ","

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        # Datas em dd/mm/aaaa não são repassadas prontas: quem converte (e
        # pode rejeitar a linha) é o `field_validator` do schema, não este
        # método — um `strptime` direto aqui derrubaria o mês inteiro se uma
        # única linha viesse malformada (mesma razão da geração horária).
        mes = bruto["MES_REFERENCIA"]
        return {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "ano_horizonte": numero_ou_nulo(bruto.get("ANO_HORIZONTE")),
            "codigo_parcela_usina": limpar(bruto.get("CODIGO_PARCELA_USINA")) or None,
            "sigla_parcela": limpar(bruto.get("SIGLA_PARCELA")),
            "tipo_combustivel": limpar(bruto.get("TIPO_COMBUSTIVEL")),
            "leilao": limpar(bruto.get("LEILAO")),
            "produto": limpar(bruto.get("PRODUTO")),
            "cvu_estrutural": numero_ou_nulo(bruto.get("CVU_ESTRUTURAL")),
            "codigo_modelo_preco": limpar(bruto.get("CODIGO_MODELO_PRECO")),
            "inicio_suprimento": bruto.get("INICIO_SUPRIMENTO"),  # o validador do schema já limpa e converte
            "termino_suprimento": bruto.get("TERMINO_SUPRIMENTO"),
        }
