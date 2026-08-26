"""Registro de conectores por nome.

`alupdata ingest bcb_cambio_ptax` resolve por aqui — sem `if/elif` por fonte
e sem import manual em cada entrypoint.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.conector import Conector

_REGISTRO: dict[str, type[Conector]] = {}


def registrar(cls: type[Conector]) -> type[Conector]:
    """Decorator de classe: registra o conector sob `fonte_entidade`."""
    rotulo = f"{cls.fonte}_{cls.entidade}"
    if rotulo in _REGISTRO and _REGISTRO[rotulo] is not cls:
        raise ValueError(f"conector duplicado: {rotulo}")
    _REGISTRO[rotulo] = cls
    return cls


def carregar_conectores() -> None:
    """Importa todos os submódulos de `src.conectores` para popular o registro."""
    import src.conectores as pacote

    for info in pkgutil.iter_modules(pacote.__path__):
        importlib.import_module(f"{pacote.__name__}.{info.name}")


def obter(rotulo: str) -> Conector:
    """Instancia o conector registrado sob `rotulo`."""
    if not _REGISTRO:
        carregar_conectores()
    if rotulo not in _REGISTRO:
        disponiveis = ", ".join(sorted(_REGISTRO)) or "nenhum"
        raise KeyError(f"conector desconhecido: {rotulo} (disponíveis: {disponiveis})")
    return _REGISTRO[rotulo]()


def listar() -> list[str]:
    """Rótulos de todos os conectores registrados."""
    if not _REGISTRO:
        carregar_conectores()
    return sorted(_REGISTRO)
