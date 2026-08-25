"""Conector IBGE — IPCA (Onda 1, API pública, sem credencial).

Fonte: SIDRA / IBGE, agregado 1737 (IPCA, Brasil).
Documentação: https://servicodados.ibge.gov.br/api/docs/agregados

Diferente do BCB em dois pontos que exercitam o framework: o período é
**mensal** (não diário) e o payload é aninhado — uma série por variável, com
os períodos como chaves de um objeto. O achatamento acontece em `extrair()`,
que devolve um registro por (período, variável).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from src.core.conector import Conector
from src.core.http import criar_sessao, get_json
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/{periodos}/variaveis/{variaveis}"

# 63 = variação mensal; 69 = variação acumulada no ano.
VARIAVEIS = ("63", "69")

# O IBGE marca período sem valor publicado com estes sentinelas.
SEM_VALOR = frozenset({"...", "..", "-", "X", ""})


class IpcaRegistro(BaseModel):
    """Uma variável do IPCA em um mês."""

    data_referencia: date
    periodo: str = Field(min_length=6, max_length=6, description="AAAAMM, como o IBGE devolve")
    variavel_id: str
    variavel: str
    unidade: str
    valor: Decimal


@registrar
class IbgeIpca(Conector):
    """IPCA mensal do Brasil. Publicado uma vez por mês, com defasagem."""

    fonte = "ibge"
    entidade = "ipca"
    schema = IpcaRegistro
    schema_versao = "1"
    max_dias_por_requisicao = None  # a API aceita o intervalo inteiro de meses

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    @staticmethod
    def _intervalo_mensal(janela: Janela) -> str:
        """Janela de datas → intervalo de meses no formato do SIDRA (AAAAMM-AAAAMM)."""
        return f"{janela.inicio:%Y%m}-{janela.fim:%Y%m}"

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        url = URL.format(periodos=self._intervalo_mensal(janela), variaveis="|".join(VARIAVEIS))
        payload = get_json(self._sessao, url, params={"localidades": "N1[all]"})

        for variavel in payload:
            for resultado in variavel.get("resultados", []):
                for serie in resultado.get("series", []):
                    for periodo, valor in serie.get("serie", {}).items():
                        if valor in SEM_VALOR:
                            continue  # mês ainda não publicado — não vira linha
                        yield {
                            "periodo": periodo,
                            "variavel_id": variavel["id"],
                            "variavel": variavel["variavel"],
                            "unidade": variavel.get("unidade", ""),
                            "valor": valor,
                        }

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        periodo = bruto["periodo"]
        return {
            "data_referencia": date(int(periodo[:4]), int(periodo[4:]), 1),
            "periodo": periodo,
            "variavel_id": bruto["variavel_id"],
            "variavel": bruto["variavel"],
            "unidade": bruto["unidade"],
            "valor": bruto["valor"],
        }
