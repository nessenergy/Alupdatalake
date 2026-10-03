"""Sondas de rede: dizem se um endereço público responde do ambiente onde o job roda.

Nasceu do CPTEC: o webservice responde 403 da máquina de desenvolvimento, e a pergunta "e de dentro do GCP?"
só se responde com a chamada saindo de lá. A lista de endereços é **constante** (nada vem de entrada do
usuário) e a sonda não grava nada: só devolve status, tamanho, tipo e os primeiros caracteres do corpo.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.core.http import criar_sessao

PREVIEW = 160
TIMEOUT_SEGUNDOS = 30

SONDAS: dict[str, tuple[str, ...]] = {
    "cptec": (
        "http://servicos.cptec.inpe.br/XML/listaCidades?city=sao%20paulo",
        "http://servicos.cptec.inpe.br/XML/cidade/7dias/244/previsao.xml",
    ),
    "inmet_previsao": ("https://apiprevmet3.inmet.gov.br/previsao/3550308",),
    "open_meteo": (
        "https://api.open-meteo.com/v1/forecast?latitude=-23.55&longitude=-46.63"
        "&daily=precipitation_sum&forecast_days=7&timezone=America%2FSao_Paulo",
    ),
}


@dataclass(frozen=True)
class ResultadoSonda:
    url: str
    status: int | None
    bytes: int
    tipo: str
    amostra: str
    erro: str | None


def sondar(nome: str, sessao=None) -> list[ResultadoSonda]:
    """Chama cada endereço da sonda `nome`. Erro de rede vira linha com `erro`, nunca exceção."""
    if nome not in SONDAS:
        raise KeyError(f"sonda desconhecida: {nome!r}; use uma de {sorted(SONDAS)}")
    sessao = sessao or criar_sessao()
    resultados = []
    for url in SONDAS[nome]:
        try:
            resposta = sessao.get(url, timeout=TIMEOUT_SEGUNDOS)
            corpo = resposta.content
            amostra = corpo[:PREVIEW].decode("utf-8", errors="replace").replace("\r", " ").replace("\n", " ")
            tipo = resposta.headers.get("Content-Type", "")
            resultados.append(ResultadoSonda(url, resposta.status_code, len(corpo), tipo, amostra, None))
        except Exception as exc:  # noqa: BLE001 - a sonda existe para registrar a falha, não para propagá-la
            resultados.append(ResultadoSonda(url, None, 0, "", "", f"{type(exc).__name__}: {str(exc)[:200]}"))
    return resultados
