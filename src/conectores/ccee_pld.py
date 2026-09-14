"""Conector CCEE — PLD horário por submercado (Onda 1, público).

Fonte: dados abertos da CCEE (CKAN), dataset `pld_horario_submercado`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/pld_horario_submercado

**Não exige credencial.** O 403 que bloqueou esta fonte desde 25/08 era filtro
de cliente não identificado, resolvido pelo `User-Agent` que o `src/core/http`
passou a enviar em toda requisição (ADR 018). As duas APIs credenciadas da CCEE
— Abertura de Mercado e Plataforma de Integração — trazem dado do agente e não
atendem a Onda 1; ficam registradas na ADR como escopo candidato.

Quinto formato do projeto, e o segundo CSV anual remoto: o caminho é o mesmo do
`ons_carga`, com três diferenças que o dado da CCEE impõe.

1. **O recurso é descoberto pelo CKAN, não escrito à mão.** O endereço de cada
   arquivo é um identificador opaco (`/e-qPA419SneVTnOQ04kEYA/content`) que muda
   quando a CCEE republica o ano. URL fixa quebraria em silêncio.
2. **O arquivo é ISO-8859-1**, não UTF-8.
3. **Não há coluna de data.** O CSV traz mês de referência e um
   `PERIODO_COMERCIALIZACAO`, que é o índice da hora dentro do mês — 1 a 744 num
   mês de 31 dias. A data e a hora são derivadas daí, e é a parte do conector
   que mais merece teste: um off-by-one desloca a série inteira.

O Brasil não observa horário de verão desde 2019, então todo mês tem
exatamente `dias × 24` períodos e a conversão é aritmética simples. Se o
horário de verão voltar, este é o ponto que quebra — e o teste de contagem de
períodos por mês é o que avisa.
"""

from __future__ import annotations

import csv
import logging
from datetime import date
from decimal import Decimal
from io import StringIO
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

from src.core.conector import Conector
from src.core.config import get_settings
from src.core.http import criar_sessao
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

CKAN_PACOTE = "https://dadosabertos.ccee.org.br/api/3/action/package_show"
DATASET = "pld_horario_submercado"

# A CCEE nomeia o submercado por extenso; o lake usa a sigla, a mesma que o ONS
# publica, para que `submercado` cruze entre as duas fontes sem tradução na
# Silver. "SUDESTE" da CCEE e "SE" do ONS são o Sudeste/Centro-Oeste.
SIGLA_SUBMERCADO = {
    "NORTE": "N",
    "NORDESTE": "NE",
    "SUL": "S",
    "SUDESTE": "SE",
}
SUBMERCADOS = frozenset(SIGLA_SUBMERCADO.values())

ENCODING = "iso-8859-1"


def _dias_no_mes(ano: int, mes: int) -> int:
    from calendar import monthrange

    return monthrange(ano, mes)[1]


def _data_e_hora(mes_referencia: str, periodo: int) -> tuple[date, int]:
    """Converte `AAAAMM` + índice horário do mês em data e hora do dia.

    O período é 1-based: o 1 é a hora 0 do dia 1, e o 25 é a hora 0 do dia 2.
    """
    ano, mes = int(mes_referencia[:4]), int(mes_referencia[4:6])
    limite = _dias_no_mes(ano, mes) * 24
    if not 1 <= periodo <= limite:
        raise ValueError(f"período {periodo} fora do mês {mes_referencia} (1..{limite})")

    deslocamento = periodo - 1
    return date(ano, mes, deslocamento // 24 + 1), deslocamento % 24


class PldHorario(BaseModel):
    """Preço de Liquidação das Diferenças de um submercado, em uma hora."""

    data_referencia: date
    hora: int = Field(ge=0, le=23, description="Hora do dia, 0 a 23, horário de Brasília")
    submercado: str
    periodo_apuracao: str
    periodo_comercializacao: int = Field(ge=1, description="Índice da hora no mês, como a CCEE publica")
    pld_reais_mwh: Decimal = Field(ge=0, description="R$/MWh; o PLD tem piso regulatório positivo")

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        sigla = valor.strip().upper()
        if sigla not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return sigla


@registrar
class CceePld(Conector):
    """PLD horário por submercado. Um CSV por ano, recortado pela janela."""

    fonte = "ccee"
    entidade = "pld"
    schema = PldHorario
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por ano de arquivo, não por dias

    def __init__(self) -> None:
        self._sessao = criar_sessao()
        self._cache_pacote: dict[str, Any] | None = None

    # ------------------------------------------------------------- descoberta

    def _pacote(self) -> dict[str, Any]:
        """Metadados do dataset no CKAN. Uma chamada por execução."""
        if self._cache_pacote is None:
            cfg = get_settings()
            resposta = self._sessao.get(CKAN_PACOTE, params={"id": DATASET}, timeout=cfg.http_timeout)
            resposta.raise_for_status()
            self._cache_pacote = resposta.json()["result"]
        return self._cache_pacote

    def _url_do_ano(self, ano: int) -> str:
        """Endereço do CSV daquele ano, como o CKAN o publica hoje."""
        sufixo = f"_{ano}"
        for recurso in self._pacote().get("resources", []):
            if str(recurso.get("name", "")).endswith(sufixo):
                return str(recurso["url"])
        raise FileNotFoundError(f"a CCEE não publica o recurso {DATASET}_{ano}")

    # ---------------------------------------------------------------- extração

    def _baixar_ano(self, ano: int) -> str:
        resposta = self._sessao.get(self._url_do_ano(ano), timeout=get_settings().http_timeout)
        resposta.raise_for_status()
        # A CCEE declara ISO-8859-1 no Content-Type, mas não em todos os
        # recursos; fixar o encoding evita acento trocado quando ela omite.
        resposta.encoding = ENCODING
        return resposta.text

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        for ano in range(janela.inicio.year, janela.fim.year + 1):
            try:
                conteudo = self._baixar_ano(ano)
            except FileNotFoundError:
                # O ano corrente só aparece depois do primeiro fechamento. Uma
                # janela que cruza o ano não pode falhar por causa disso.
                logger.warning("CCEE PLD: %d ainda não publicado, ignorado", ano)
                continue

            logger.info("CCEE PLD: lendo %d", ano)
            for linha in csv.DictReader(StringIO(conteudo), delimiter=";"):
                mes = (linha.get("MES_REFERENCIA") or "").strip()
                periodo = (linha.get("PERIODO_COMERCIALIZACAO") or "").strip()
                if len(mes) != 6 or not periodo.isdigit():
                    continue  # linha em branco ou rodapé; a validação conta o resto

                try:
                    dia, _hora = _data_e_hora(mes, int(periodo))
                except ValueError:
                    logger.warning("CCEE PLD: período inválido descartado: %s/%s", mes, periodo)
                    continue

                if janela.inicio <= dia <= janela.fim:
                    yield linha  # o arquivo é anual; a janela é o recorte pedido

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"].strip()
        periodo = int(bruto["PERIODO_COMERCIALIZACAO"])
        dia, hora = _data_e_hora(mes, periodo)
        nome = (bruto.get("SUBMERCADO") or "").strip().upper()

        return {
            "data_referencia": dia,
            "hora": hora,
            # Nome desconhecido passa adiante como veio: quem recusa é o schema,
            # com o nome original na mensagem, não um KeyError sem contexto.
            "submercado": SIGLA_SUBMERCADO.get(nome, nome),
            "periodo_apuracao": f"{mes[:4]}-{mes[4:6]}",
            "periodo_comercializacao": periodo,
            "pld_reais_mwh": bruto["PLD"],
        }
