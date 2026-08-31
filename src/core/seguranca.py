"""Redação de informações sensíveis antes de log ou persistência."""

from __future__ import annotations

import re

_REGRAS = (
    (re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+|bearer\s+)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)([a-z][a-z0-9+.-]*://)[^/@\s]+@"), r"\1[REDACTED]@"),
    (
        re.compile(r"(?i)([?&](?:api[_-]?token|api[_-]?key|access[_-]?token|password|senha)=)[^&\s]+"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r'(?i)(["\']?(?:password|senha|token|api[_-]?key)["\']?\s*[:=]\s*)["\']?[^\s,;}"\']+'),
        r"\1[REDACTED]",
    ),
)


def sanitizar(valor: object, *, limite: int = 2000) -> str:
    """Remove padrões de credencial e limita o texto destinado a observabilidade."""
    texto = str(valor)
    for padrao, substituicao in _REGRAS:
        texto = padrao.sub(substituicao, texto)
    if len(texto) > limite:
        sufixo = "… [TRUNCATED]"
        texto = texto[: limite - len(sufixo)] + sufixo
    return texto
