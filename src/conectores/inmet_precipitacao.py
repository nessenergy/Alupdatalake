"""Conector INMET — precipitação horária por estação (Onda 1, dado público, sem credencial).

Fonte: zip anual do portal, `https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip`, com um CSV por
estação (595 em 2025). Cada CSV tem 8 linhas de metadados, o cabeçalho na linha 9, `;` como separador, vírgula
decimal e codificação latin-1. Só a coluna de precipitação horária interessa à Onda 1.

A API `apitempo.inmet.gov.br` não serve para o histórico: a lista de estações responde, o dado horário voltou
204 (vazio). O zip do ano corrente é parcial e atrasa (o de 2026 tinha `Last-Modified` de 02/09/2026 em 02/10),
então uma janela recente pode vir com menos horas do que se espera; a Gold expõe a última hora com dado.
"""

from __future__ import annotations

import logging
import tempfile
import zipfile
from datetime import date
from decimal import Decimal
from typing import IO, TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

from src.core.conector import Conector
from src.core.http import criar_sessao
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip"
LINHAS_DE_METADADOS = 8  # o cabeçalho das colunas é a linha 9
COLUNA_PRECIPITACAO = 2
SENTINELA_SEM_MEDICAO = "-9999"
PRECIPITACAO_MAXIMA_MM = Decimal("500")  # o recorde horário do país é da ordem de 200 mm; acima disso é erro

logger = logging.getLogger(__name__)


class LayoutInesperadoError(RuntimeError):
    """O zip ou o CSV não têm a forma que o conector conhece."""


def _decimal_br(valor: Any) -> Any:
    return valor.replace(",", ".") if isinstance(valor, str) else valor


class PrecipitacaoHoraria(BaseModel):
    """A chuva de uma hora em uma estação. `precipitacao_mm` nulo é hora sem medição, nunca zero."""

    estacao: str
    nome_estacao: str
    regiao: str
    uf: str
    latitude: Decimal
    longitude: Decimal
    altitude_m: Decimal | None = None
    data_referencia: date
    hora_utc: int = Field(ge=0, le=23)
    precipitacao_mm: Decimal | None = Field(default=None, ge=0, le=PRECIPITACAO_MAXIMA_MM)

    @field_validator("latitude", "longitude", "altitude_m", "precipitacao_mm", mode="before")
    @classmethod
    def _numero_da_origem(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            texto = valor.strip()
            if texto in {"", SENTINELA_SEM_MEDICAO}:
                return None
            return _decimal_br(texto)
        return valor


def _metadados(linhas: list[str]) -> dict[str, str]:
    meta = {}
    for linha in linhas[:LINHAS_DE_METADADOS]:
        chave, _, valor = linha.partition(":;")
        meta[chave.strip()] = valor.strip()
    return meta


def _ler_estacao(conteudo: bytes) -> Iterator[dict[str, Any]]:
    linhas = conteudo.decode("latin-1").splitlines()
    meta = _metadados(linhas)
    for chave in ("REGIAO", "UF", "ESTACAO", "CODIGO (WMO)", "LATITUDE", "LONGITUDE"):
        if not meta.get(chave):
            raise LayoutInesperadoError(f"CSV de estação sem o metadado {chave!r}")
    for linha in linhas[LINHAS_DE_METADADOS + 1 :]:
        campos = linha.split(";")
        if len(campos) <= COLUNA_PRECIPITACAO or not campos[0].strip():
            continue
        yield {
            "estacao": meta["CODIGO (WMO)"],
            "nome_estacao": meta["ESTACAO"],
            "regiao": meta["REGIAO"],
            "uf": meta["UF"],
            "latitude": meta["LATITUDE"],
            "longitude": meta["LONGITUDE"],
            "altitude_m": meta.get("ALTITUDE"),
            "data": campos[0].strip(),  # 2025/01/01
            "hora": campos[1].strip(),  # 0100 UTC
            "precipitacao_mm": campos[COLUNA_PRECIPITACAO],
        }


@registrar
class InmetPrecipitacao(Conector):
    """Precipitação horária. Um zip por ano, recortado pela janela."""

    fonte = "inmet"
    entidade = "precipitacao"
    schema = PrecipitacaoHoraria
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por ano de arquivo, não por dias

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _baixar_zip(self, ano: int) -> IO[bytes] | None:
        """Baixa o zip do ano para um arquivo temporário (são 60 a 90 MB). `None` quando o ano ainda não existe."""
        from src.core.config import get_settings

        resposta = self._sessao.get(URL.format(ano=ano), timeout=get_settings().http_timeout, stream=True)
        if resposta.status_code == 404:
            return None
        resposta.raise_for_status()
        arquivo = tempfile.TemporaryFile()  # noqa: SIM115 — fechado pelo chamador
        for pedaco in resposta.iter_content(1 << 20):
            arquivo.write(pedaco)
        arquivo.seek(0)
        return arquivo

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        inicio, fim = janela.inicio.isoformat(), janela.fim.isoformat()
        for ano in range(janela.inicio.year, janela.fim.year + 1):
            arquivo = self._baixar_zip(ano)
            if arquivo is None:
                logger.warning("INMET: zip de %d ainda não publicado", ano)
                continue
            with arquivo, zipfile.ZipFile(arquivo) as z:
                csvs = [n for n in z.namelist() if n.upper().endswith(".CSV")]
                if not csvs:
                    raise LayoutInesperadoError(f"o zip de {ano} do INMET não tem nenhum CSV")
                for nome in csvs:
                    for linha in _ler_estacao(z.read(nome)):
                        dia = linha["data"].replace("/", "-")
                        if inicio <= dia <= fim:
                            yield linha

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            **{k: bruto[k] for k in ("estacao", "nome_estacao", "regiao", "uf", "latitude", "longitude", "altitude_m")},
            "data_referencia": bruto["data"].replace("/", "-"),
            "hora_utc": int(bruto["hora"][:2]),
            "precipitacao_mm": bruto["precipitacao_mm"],
        }
