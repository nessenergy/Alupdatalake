"""Conector ONS — geração horária por usina (Onda 1, público).

Fonte: Dados Abertos ONS, dataset `geracao_usina_2_ho`, um CSV por mês.
Documentação: https://dados.ons.org.br/dataset/geracao-usina-2

Molde do `ons_carga` (CSV remoto direto, sem CKAN), com uma diferença: aqui o
recurso é **mensal**, não anual — a janela decide quais meses baixar, e as
linhas fora do intervalo pedido são descartadas na extração, como no `ons_carga`.

Junto do `ons_capacidade`, é a segunda fonte a trazer a coluna `ceg`: a issue
#141 pede um de-para de quatro colunas (sigla interna ↔ CEG ↔ nome CCEE ↔ nome
ONS) que hoje só o `aneel_siga` alimenta pelo lado CEG. Estas duas fontes
entregam o lado CEG ↔ nome ONS sem depender de ninguém — ver o dicionário de
dados.
"""

from __future__ import annotations

import csv
import logging
from datetime import date, datetime
from decimal import Decimal
from io import StringIO
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator, model_validator

from src.conectores.ons_carga import SUBMERCADOS
from src.core.conector import Conector
from src.core.http import criar_sessao
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/GERACAO_USINA-2_{ano}_{mes:02d}.csv"

logger = logging.getLogger(__name__)


def _meses(janela: Janela) -> list[tuple[int, int]]:
    """(ano, mês) de cada mês entre o início e o fim da janela, inclusive."""
    meses: list[tuple[int, int]] = []
    ano, mes = janela.inicio.year, janela.inicio.month
    fim = (janela.fim.year, janela.fim.month)
    while (ano, mes) <= fim:
        meses.append((ano, mes))
        ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
    return meses


def _texto_ou_nulo(valor: str | None) -> str | None:
    """Vazio ou "-" na origem é ausência de CEG/id, não um valor literal."""
    texto = (valor or "").strip()
    return texto if texto and texto != "-" else None


class GeracaoUsina(BaseModel):
    """A geração de uma usina em uma hora do mês publicado.

    `data_referencia` e `hora` não vêm prontos: são derivados de
    `din_instante` pelo `model_validator` no fim da classe — a mesma razão do
    `ccee_geracao_usina`, para que um timestamp malformado vire
    `linhas_invalidas`, não um crash em `transformar()`.
    """

    din_instante: str = Field(exclude=True)  # cru; só deriva data_referencia/hora
    data_referencia: date | None = None
    hora: int | None = None
    submercado: str
    nome_subsistema: str
    uf: str
    nome_uf: str
    modalidade_operacao: str
    tipo_usina: str
    tipo_combustivel: str
    nome_usina: str
    id_ons: str | None = None
    codigo_usina: str | None = None  # CEG — dimensão comum do projeto (achado #141)
    # Pode ser zero, e pode ser negativo (usina reversível / medição). Também
    # pode vir **vazio** na origem — ~12% das linhas do arquivo real de
    # julho/2026 (63.576 de 533.832) — para a usina sem geração medida naquela
    # hora; vazio é ausência, não erro, e vira NULL em vez de descartar a linha.
    geracao_mw: Decimal | None = None

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        sigla = valor.strip().upper()
        if sigla not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return sigla

    @field_validator("id_ons", "codigo_usina", mode="before")
    @classmethod
    def _vazio_ou_traco_e_nulo(cls, valor: str | None) -> str | None:
        return _texto_ou_nulo(valor)

    @field_validator("geracao_mw", mode="before")
    @classmethod
    def _vazio_e_nulo(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            texto = valor.strip()
            return texto or None
        return valor

    @model_validator(mode="after")
    def _deriva_data_e_hora(self) -> GeracaoUsina:
        try:
            instante = datetime.strptime(self.din_instante, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError(f"din_instante inválido: {self.din_instante!r}") from exc
        self.data_referencia = instante.date()
        self.hora = instante.hour
        return self


@registrar
class OnsGeracaoUsina(Conector):
    """Geração horária por usina. Um CSV por mês, filtrado pela janela."""

    fonte = "ons"
    entidade = "geracao_usina"
    schema = GeracaoUsina
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por mês de arquivo, não por dias

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _baixar_mes(self, ano: int, mes: int) -> str:
        from src.core.config import get_settings

        resposta = self._sessao.get(URL.format(ano=ano, mes=mes), timeout=get_settings().http_timeout)
        resposta.raise_for_status()
        return resposta.text

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        for ano, mes in _meses(janela):
            logger.info("ONS geração de usina: baixando %d-%02d", ano, mes)
            leitor = csv.DictReader(StringIO(self._baixar_mes(ano, mes)), delimiter=";")
            for linha in leitor:
                instante = linha.get("din_instante", "")[:10]
                if not instante:
                    continue
                if not (janela.inicio.isoformat() <= instante <= janela.fim.isoformat()):
                    continue  # o arquivo é mensal; a janela é o recorte pedido
                yield linha

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "din_instante": bruto.get("din_instante", ""),
            "submercado": bruto.get("id_subsistema", ""),
            "nome_subsistema": bruto.get("nom_subsistema", "").strip(),
            "uf": bruto.get("id_estado", "").strip(),
            "nome_uf": bruto.get("nom_estado", "").strip(),
            "modalidade_operacao": bruto.get("cod_modalidadeoperacao", "").strip(),
            "tipo_usina": bruto.get("nom_tipousina", "").strip(),
            "tipo_combustivel": bruto.get("nom_tipocombustivel", "").strip(),
            "nome_usina": bruto.get("nom_usina", "").strip(),
            "id_ons": bruto.get("id_ons"),
            "codigo_usina": bruto.get("ceg"),
            "geracao_mw": bruto.get("val_geracao"),
        }
