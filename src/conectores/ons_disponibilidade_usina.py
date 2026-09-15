"""Conector ONS — disponibilidade horária por usina (Onda 1, público).

Fonte: Dados Abertos ONS, dataset `disponibilidade_usina_ho`, um CSV por mês.
Documentação: https://dados.ons.org.br/dataset/disponibilidade_usina

Mesmo molde do `ons_geracao_usina`: recurso mensal, janela recortando as linhas
na extração. É a terceira peça do retrato do parque despachado — o cadastro diz
**quais usinas existem** (`aneel_siga`), a capacidade diz **quanto poderiam
gerar** (`ons_capacidade`), a geração diz **quanto geraram**
(`ons_geracao_usina`), e esta diz **quanto estavam aptas a gerar naquela hora**.
Sem ela, não dá para distinguir usina parada de usina sem despacho.

Cobre só o parque despachado centralmente — em agosto/2026 o arquivo trouxe
UHE, UTE e UTN, e nenhuma eólica ou solar. O CEG vem preenchido em 100% das
linhas, então esta fonte entra inteira no `gold.de_para_usina`.
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
from src.conectores.ons_geracao_usina import _meses, _texto_ou_nulo
from src.core.ceg import ceg_canonico
from src.core.conector import Conector
from src.core.http import criar_sessao
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = (
    "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/disponibilidade_usina_ho/"
    "DISPONIBILIDADE_USINA_{ano}_{mes:02d}.csv"
)

logger = logging.getLogger(__name__)


def _vazio_e_nulo(valor: Any) -> Any:
    """Campo numérico vazio é ausência de medida, não zero.

    Zero aqui é informação de peso — usina indisponível é exatamente o que esta
    fonte existe para mostrar —, então zero nunca pode virar NULL no caminho.
    """
    if isinstance(valor, str):
        texto = valor.strip()
        return texto or None
    return valor


class DisponibilidadeUsina(BaseModel):
    """A disponibilidade de uma usina em uma hora do mês publicado.

    `data_referencia` e `hora` são derivados de `din_instante` no
    `model_validator`, como no `ons_geracao_usina`: timestamp malformado vira
    `linhas_invalidas`, não crash em `transformar()`.
    """

    din_instante: str = Field(exclude=True)  # cru; só deriva data_referencia/hora
    data_referencia: date | None = None
    hora: int | None = None
    submercado: str
    nome_subsistema: str
    uf: str
    nome_uf: str
    tipo_usina: str  # UHE, UTE, UTN — o parque despachado centralmente
    tipo_combustivel: str
    nome_usina: str
    id_ons: str | None = None
    codigo_usina: str | None = None  # CEG na forma canônica (src/core/ceg.py)
    potencia_instalada: Decimal | None = None
    disponibilidade_operacional: Decimal | None = None
    disponibilidade_sincronizada: Decimal | None = None

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        sigla = valor.strip().upper()
        if sigla not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return sigla

    @field_validator("id_ons", mode="before")
    @classmethod
    def _vazio_ou_traco_e_nulo(cls, valor: str | None) -> str | None:
        return _texto_ou_nulo(valor)

    @field_validator("codigo_usina", mode="before")
    @classmethod
    def _ceg_na_forma_canonica(cls, valor: str | None) -> str | None:
        return ceg_canonico(valor)

    @field_validator(
        "potencia_instalada",
        "disponibilidade_operacional",
        "disponibilidade_sincronizada",
        mode="before",
    )
    @classmethod
    def _numero_vazio_e_nulo(cls, valor: Any) -> Any:
        return _vazio_e_nulo(valor)

    @model_validator(mode="after")
    def _deriva_data_e_hora(self) -> DisponibilidadeUsina:
        try:
            instante = datetime.strptime(self.din_instante, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError(f"din_instante inválido: {self.din_instante!r}") from exc
        self.data_referencia = instante.date()
        self.hora = instante.hour
        return self


@registrar
class OnsDisponibilidadeUsina(Conector):
    """Disponibilidade horária por usina. Um CSV por mês, filtrado pela janela."""

    fonte = "ons"
    entidade = "disponibilidade_usina"
    schema = DisponibilidadeUsina
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
            logger.info("ONS disponibilidade de usina: baixando %d-%02d", ano, mes)
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
            "tipo_usina": bruto.get("id_tipousina", "").strip(),
            "tipo_combustivel": bruto.get("nom_tipocombustivel", "").strip(),
            "nome_usina": bruto.get("nom_usina", "").strip(),
            "id_ons": bruto.get("id_ons"),
            "codigo_usina": bruto.get("ceg"),
            "potencia_instalada": bruto.get("val_potenciainstalada"),
            "disponibilidade_operacional": bruto.get("val_dispoperacional"),
            "disponibilidade_sincronizada": bruto.get("val_dispsincronizada"),
        }
