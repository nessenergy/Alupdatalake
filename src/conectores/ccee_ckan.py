"""Base dos conectores de CSV da CCEE publicados no CKAN (dados abertos).

A ADR 018 destravou a via pública; a ADR 021 escolheu 24 conjuntos e a ordem.
Cada conjunto vira uma subclasse desta base com três coisas: o nome do dataset,
o schema Pydantic e o `transformar()`. O resto — descobrir o recurso no CKAN,
baixar em fluxo, descomprimir, decodificar e recortar pela janela — é o mesmo
para todos, e foi lido dos arquivos reais em 14/09/2026.

## O que a leitura dos arquivos impôs

1. **Encoding misto no mesmo arquivo.** `lista_agente_associado_2026` tem
   49.269 linhas em UTF-8 e 98.532 em ISO-8859-1. Um `resposta.encoding` só
   mutila metade em silêncio; por isso a decodificação é **por linha**.
2. **Gzip mensal.** `geracao_horaria_usina` vem em recursos `_AAAAMM` de 61 MB
   comprimidos (~800 MB de texto). O arquivo não cabe em `resposta.text`; a
   leitura é em fluxo, e o gzip é detectado pelos dois primeiros bytes.
3. **Delimitador não é sempre `;`.** `custo_variavel_unitario_estrutural` usa
   vírgula.
4. **A janela recorta por mês.** A CCEE publica por `MES_REFERENCIA`; uma
   janela de 120 dias cobre a recontabilização (ADR 016) sem baixar o histórico
   inteiro a cada execução.

`ccee_pld` continua com a própria descoberta: tem 17 testes e um recorte por
dia que nenhuma entidade mensal usa. Migrá-lo é tarefa à parte.
"""

from __future__ import annotations

import csv
import gzip
import io
import logging
from datetime import date, datetime
from typing import IO, TYPE_CHECKING, Any, ClassVar, Literal

from src.core.conector import Conector
from src.core.config import get_settings
from src.core.http import criar_sessao

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

CKAN_PACOTE = "https://dadosabertos.ccee.org.br/api/3/action/package_show"
_GZIP_MAGIC = b"\x1f\x8b"


class _SemErroAoFechar:
    """Envelope do fluxo bruto: leitura após o corpo terminar vira EOF, não erro.

    urllib3 fecha a conexão assim que o corpo termina de chegar; o
    `io.BufferedReader` (e, por cima dele, o `gzip.GzipFile`, que sempre faz
    uma leitura a mais para conferir o rodapé do arquivo) ainda tenta uma
    leitura extra para confirmar que não há mais dado, e essa leitura extra
    batia num `ValueError: read of closed file` em vez de um EOF limpo — visto
    contra a API real da CCEE em 14/09/2026 (`lista_agente_associado_2026`,
    que a CDN entrega com `Content-Encoding: gzip`). Fica por baixo do
    `BufferedReader` — não por cima — porque só assim o `readinto` devolve 0
    (EOF) antes do `BufferedReader` propagar a exceção e descartar o que já
    tinha em buffer.
    """

    def __init__(self, bruto: IO[bytes]) -> None:
        self._bruto = bruto

    def readable(self) -> bool:
        return True

    @property
    def closed(self) -> bool:
        return False

    def close(self) -> None:
        self._bruto.close()

    def flush(self) -> None:
        pass

    def readinto(self, b: bytearray) -> int:
        try:
            dado = self._bruto.read(len(b))
        except ValueError:
            # Só engole a leitura pós-fechamento (confirmado contra a API real:
            # nesse instante `self._bruto.closed` já é True). Qualquer outro
            # `ValueError` — de origem diferente — sobe, para uma leitura
            # truncada nunca virar EOF limpo em silêncio (regra 4: Bronze
            # completo, não parcial-disfarçado-de-sucesso).
            if getattr(self._bruto, "closed", False):
                return 0
            raise
        b[: len(dado)] = dado
        return len(dado)


def decodificar(linha: bytes) -> str:
    """UTF-8 quando a linha é UTF-8 válido; ISO-8859-1 no resto.

    Uma sequência ISO-8859-1 raramente é UTF-8 válido por acaso (precisaria de
    dois acentos consecutivos com bytes específicos); o custo desse caso raro é
    um caractere trocado numa razão social, não uma linha perdida.
    """
    try:
        return linha.decode("utf-8")
    except UnicodeDecodeError:
        return linha.decode("iso-8859-1")


def limpar(valor: str | None) -> str:
    """Texto da CCEE sem espaço em volta, inclusive o não separável (`\\xa0`)."""
    return (valor or "").replace("\xa0", " ").strip()


def numero_ou_nulo(valor: str | None) -> str | None:
    """Vazio na origem é ausência, não zero. Zero continua zero."""
    texto = limpar(valor)
    return texto if texto else None


def primeiro_dia(mes_referencia: str) -> date:
    """`AAAAMM` → primeiro dia do mês. É a `data_referencia` das entidades mensais."""
    mes = limpar(mes_referencia)
    if len(mes) != 6 or not mes.isdigit():
        raise ValueError(f"MES_REFERENCIA inválido: {mes_referencia!r}")
    return date(int(mes[:4]), int(mes[4:6]), 1)


def periodo_ccee(mes_referencia: str) -> str:
    """`AAAAMM` → `AAAA-MM`, o `periodo_apuracao_ccee` (o que a origem declara)."""
    dia = primeiro_dia(mes_referencia)
    return f"{dia.year:04d}-{dia.month:02d}"


def _meses(inicio: date, fim: date) -> list[str]:
    """`AAAAMM` de cada mês entre inicio e fim, inclusive."""
    meses = []
    ano, mes = inicio.year, inicio.month
    while (ano, mes) <= (fim.year, fim.month):
        meses.append(f"{ano:04d}{mes:02d}")
        ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
    return meses


class CceeCsvCkan(Conector):
    """Um conjunto do CKAN da CCEE, CSV por ano ou gzip por mês.

    A subclasse define `dataset`, `entidade`, `schema`, opcionalmente
    `delimitador` e `recurso_por`, e implementa `transformar()`. O bruto que
    chega em `transformar()` traz as colunas do CSV e mais duas chaves
    técnicas: `_versao_publicacao` (ISO, do CKAN) e `_sufixo` (o recurso).
    """

    dataset: ClassVar[str]
    delimitador: ClassVar[str] = ";"
    recurso_por: ClassVar[Literal["ano", "mes"]] = "ano"

    fonte = "ccee"
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por recurso, não por dias

    def __init__(self) -> None:
        self._sessao = criar_sessao()
        self._cache_pacote: dict[str, Any] | None = None

    # ------------------------------------------------------------- descoberta

    def _pacote(self) -> dict[str, Any]:
        """Metadados do dataset no CKAN. Uma chamada por execução."""
        if self._cache_pacote is None:
            cfg = get_settings()
            resposta = self._sessao.get(CKAN_PACOTE, params={"id": self.dataset}, timeout=cfg.http_timeout)
            resposta.raise_for_status()
            self._cache_pacote = resposta.json()["result"]
        return self._cache_pacote

    def _recurso(self, sufixo: str) -> dict[str, Any]:
        """O recurso cujo nome termina em `_<sufixo>`, como o CKAN o publica hoje."""
        alvo = f"_{sufixo}"
        for recurso in self._pacote().get("resources", []):
            if str(recurso.get("name", "")).endswith(alvo):
                return recurso
        raise FileNotFoundError(f"a CCEE não publica o recurso {self.dataset}_{sufixo}")

    def publicado_em(self, sufixo: str) -> date:
        """`last_modified` do recurso: o identificador de versão da ADR 016 (opção B)."""
        publicado = str(self._recurso(sufixo).get("last_modified") or "")[:10]
        try:
            return date.fromisoformat(publicado)
        except ValueError:
            hoje = datetime.now().date()
            logger.warning(
                "CCEE %s: recurso %s sem last_modified; versao_publicacao assumida como %s", self.dataset, sufixo, hoje
            )
            return hoje

    # ---------------------------------------------------------------- leitura

    def _abrir(self, sufixo: str) -> IO[bytes]:
        """Fluxo binário do recurso. É o seam dos testes: eles devolvem um BytesIO.

        O envelope `_SemErroAoFechar` fica por baixo do `BufferedReader` — veja
        a docstring dele — porque a CDN da CCEE fecha a conexão assim que o
        corpo termina de chegar (visto contra a API real em 14/09/2026, no
        `lista_agente_associado_2026`, que ela serve com `Content-Encoding:
        gzip`).
        """
        resposta = self._sessao.get(self._recurso(sufixo)["url"], stream=True, timeout=get_settings().http_timeout)
        resposta.raise_for_status()
        return io.BufferedReader(_SemErroAoFechar(resposta.raw))  # type: ignore[arg-type]

    def _linhas(self, fluxo: IO[bytes]) -> Iterator[dict[str, str]]:
        if not hasattr(fluxo, "peek"):
            fluxo = io.BufferedReader(_SemErroAoFechar(fluxo))  # o BytesIO dos testes não tem peek
        if fluxo.peek(2)[:2] == _GZIP_MAGIC:
            fluxo = gzip.GzipFile(fileobj=fluxo)  # type: ignore[assignment]
        texto = (decodificar(linha).rstrip("\r\n") for linha in fluxo)
        yield from csv.DictReader(texto, delimiter=self.delimitador)

    def _sufixos(self, janela: Janela) -> list[str]:
        if self.recurso_por == "mes":
            return _meses(janela.inicio, janela.fim)
        return [str(ano) for ano in range(janela.inicio.year, janela.fim.year + 1)]

    @staticmethod
    def _dentro(mes_referencia: str, janela: Janela) -> bool:
        mes = limpar(mes_referencia)
        if len(mes) != 6 or not mes.isdigit():
            return False  # linha em branco ou rodapé; a validação conta o resto
        chave = (int(mes[:4]), int(mes[4:6]))
        return (janela.inicio.year, janela.inicio.month) <= chave <= (janela.fim.year, janela.fim.month)

    # ---------------------------------------------------------------- extração

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        for sufixo in self._sufixos(janela):
            try:
                fluxo = self._abrir(sufixo)
            except FileNotFoundError:
                # O período corrente só aparece depois do fechamento. Janela que
                # o alcança não pode falhar por isso.
                logger.warning("CCEE %s: recurso %s ainda não publicado, ignorado", self.dataset, sufixo)
                continue

            logger.info("CCEE %s: lendo %s", self.dataset, sufixo)
            # `publicado_em` só é chamado se alguma linha realmente cair dentro
            # da janela — um sufixo sem linha aproveitável (ex.: mês corrente
            # ainda vazio) não precisa de uma segunda consulta ao CKAN.
            versao: str | None = None
            for linha in self._linhas(fluxo):
                if self._dentro(linha.get("MES_REFERENCIA", ""), janela):
                    if versao is None:
                        versao = self.publicado_em(sufixo).isoformat()
                    # As duas chaves técnicas viajam no bruto para chegar ao raw:
                    # sem elas o arquivo no GCS não diria de qual publicação é.
                    yield linha | {"_versao_publicacao": versao, "_sufixo": sufixo}
