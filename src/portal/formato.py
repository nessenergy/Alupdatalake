"""Formatação de número e de tempo para quem lê — compartilhada pelas telas."""

from __future__ import annotations

from src.portal.grafico import _milhar as milhar

__all__ = ["bytes_humano", "duracao", "milhar", "pct"]


def duracao(minutos: int | None) -> str:
    """Minutos como algo que uma pessoa lê sem converter de cabeça."""
    if minutos is None:
        return "—"
    if minutos < 90:
        return f"há {minutos} min"
    if minutos < 60 * 36:
        return f"há {minutos // 60} h"
    return f"há {minutos // 1440} dias"


def pct(valor: float | None, casas: int = 1) -> str:
    return "—" if valor is None else f"{valor * 100:.{casas}f}%".replace(".", ",")


def bytes_humano(valor: int) -> str:
    """Byte varrido só significa alguma coisa na unidade em que se cobra."""
    for unidade, divisor in (("TiB", 1024**4), ("GiB", 1024**3), ("MiB", 1024**2)):
        if valor >= divisor:
            return f"{valor / divisor:.2f} {unidade}".replace(".", ",")
    return f"{milhar(valor)} B"
