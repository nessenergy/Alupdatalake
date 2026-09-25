"""Acesso a bancos relacionais das fontes internas (Onda 3).

O equivalente de `http.py` para fonte que não fala HTTP: abre conexão a partir
de uma DSN guardada no Secret Manager e devolve linhas como dicionários, no
mesmo formato que `extrair()` já entrega ao runner.

Drivers em modo puro-Python (`oracledb` *thin*, `pymysql`, `pytds`): a imagem
não precisa de Oracle Instant Client, `libmysqlclient` nem driver ODBC. Ficam em
`[project.optional-dependencies].bancos` — conector de API pública não paga por
eles.

Formato da DSN, uma linha no secret `alupdata-<fonte>-dsn`:

    oracle://usuario:senha@host:1521/SERVICO
    mysql://usuario:senha@host:3306/base?ssl_ca=/caminho/da/ca.pem
    sqlserver://usuario:senha@host:1433/base

O SQL Server entrou pela via (c) do adendo ao C4: a Alup já mantém o realizado
do Balanço Energético da CCEE num SQL Server, alimentado por processo mensal
manual. Ler dali não depende do desbloqueio do portal da CCEE, e pode dar origem
à dimensão `agente_ccee`. Escolhemos `pytds` por ser puro-Python; a alternativa
usual (`pyodbc`) exigiria driver de sistema na imagem.

Limite conhecido: `Conector._ingerir` materializa o resultado de `extrair()`
numa lista antes de validar. `consultar()` pagina no cursor — o que protege o
banco de origem e a rede sob VPN —, mas o processo ainda segura todas as linhas
da janela em memória. Para o FMB, isso significa manter a janela curta
(`max_dias_por_requisicao`) até que o runner passe a carregar em lotes.
"""

from __future__ import annotations

import logging
import re
import ssl
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, unquote, urlparse

from src.core.config import get_settings
from src.core.secrets import ler_secret

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)

PORTA_PADRAO = {"oracle": 1521, "mysql": 3306, "sqlserver": 1433}
_HOSTS_LOCAIS = {"127.0.0.1", "localhost", "::1"}
_SOMENTE_LEITURA = re.compile(r"^\s*(?:--[^\n]*\n\s*)*(SELECT|WITH)\b", re.IGNORECASE)


def conectar(dsn: str) -> Any:
    """Conexão DB-API a partir da DSN.

    A DSN carrega a senha: nenhuma mensagem de erro daqui pode ecoá-la, nem
    inteira nem em pedaços (cláusula 8.5).
    """
    url = urlparse(dsn)
    cfg = get_settings()
    porta = url.port or PORTA_PADRAO.get(url.scheme, 0)
    base = unquote(url.path).lstrip("/")

    if url.scheme == "oracle":
        import oracledb  # import tardio: conector de API pública não instala driver de banco

        return oracledb.connect(
            user=unquote(url.username or ""),
            password=unquote(url.password or ""),
            dsn=f"{url.hostname}:{porta}/{base}",
            tcp_connect_timeout=cfg.banco_timeout,
        )

    if url.scheme == "mysql":
        import pymysql

        return pymysql.connect(
            host=url.hostname,
            port=porta,
            user=unquote(url.username or ""),
            password=unquote(url.password or ""),
            database=base,
            connect_timeout=int(cfg.banco_timeout),
            **_tls_mysql(url.hostname or "", parse_qs(url.query)),
        )

    if url.scheme == "sqlserver":
        import pytds

        return pytds.connect(
            server=url.hostname,
            port=porta,
            user=unquote(url.username or ""),
            password=unquote(url.password or ""),
            database=base,
            login_timeout=int(cfg.banco_timeout),
            as_dict=False,  # `consultar()` monta o dicionário a partir de cursor.description
        )

    # Só o esquema entra na mensagem — usuário, host e senha ficam de fora.
    raise ValueError(f"driver não suportado: {url.scheme!r}; use 'oracle', 'mysql' ou 'sqlserver'")


def _tls_mysql(host: str, consulta: dict[str, list[str]]) -> dict[str, Any]:
    """TLS obrigatório, com certificado e host verificados (ADR 013, revisão de 11/09).

    O MySQL RDS é lido pela internet, sem VPN. A CA vem de `?ssl_ca=<caminho>` na
    DSN — a do RDS não está no repositório de CAs do sistema. `?tls=0` só vale
    para banco local, como os contêineres de `tests/integration`.
    """
    if consulta.get("tls") == ["0"]:
        if host not in _HOSTS_LOCAIS:
            # Nem host nem usuário na mensagem: a DSN inteira é segredo.
            raise ValueError("TLS só pode ser desligado (tls=0) para banco local")
        return {"ssl_disabled": True}
    return {"ssl": ssl.create_default_context(cafile=consulta.get("ssl_ca", [None])[0])}


def criar_conexao(fonte: str, campo: str = "dsn") -> Any:
    """Conexão da fonte, com a DSN lida do Secret Manager."""
    return conectar(ler_secret(fonte, campo))


@contextmanager
def abrir_conexao(fonte: str, campo: str = "dsn") -> Iterator[Any]:
    """Abre e fecha uma conexão da fonte mesmo quando a consulta falha."""
    conexao = criar_conexao(fonte, campo)
    try:
        yield conexao
    finally:
        conexao.close()


def consultar(
    conexao: Any,
    sql: str,
    parametros: dict[str, Any] | None = None,
    lote: int | None = None,
) -> Iterator[dict[str, Any]]:
    """Executa `sql` e devolve uma linha por vez, como dicionário.

    Pagina no cursor (`fetchmany`) em vez de `fetchall`: uma tabela de anos do
    FMB não cabe confortavelmente na memória do Cloud Run Job, e o
    `arraysize` também define quantos round-trips a VPN paga.

    Os nomes de coluna vêm em minúsculas — Oracle os devolve em maiúsculas, e o
    resto do framework trabalha em `snake_case`.
    """
    if not _SOMENTE_LEITURA.match(sql):
        raise ValueError("consulta de origem deve ser somente leitura (SELECT ou WITH)")
    tamanho = lote or get_settings().banco_lote
    cursor = conexao.cursor()
    try:
        cursor.execute(sql, parametros or {})
        colunas = [descricao[0].lower() for descricao in cursor.description]
        while linhas := cursor.fetchmany(tamanho):
            for linha in linhas:
                yield dict(zip(colunas, linha, strict=True))
    finally:
        cursor.close()
