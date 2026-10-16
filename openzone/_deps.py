"""Import pigro delle dipendenze opzionali.

OpenZone dichiara molte librerie, ma nessuna applicazione le vuole tutte: chi
interroga il glossario non deve installare ``mplsoccer``, e chi lavora su DataFrame
non deve installare ``duckdb``. Questo modulo centralizza l'import ritardato e
trasforma un :class:`ModuleNotFoundError` in un errore azionabile che dice all'utente
quale extra installare.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any

from openzone.exceptions import MissingDependencyError

__all__ = ["require", "has"]

#: Mappa nome-modulo -> extra di ``pyproject.toml`` che lo fornisce.
EXTRA_BY_MODULE: dict[str, str] = {
    "duckdb": "warehouse",
    "kloppy": "standardize",
    "matplotlib": "viz",
    "mplsoccer": "viz",
    "networkx": "spatial",
    "pyarrow": "ingest",
    "requests": "ingest",
    "scraperfc": "ingest",
    "sklearn": "models",
    "socceraction": "standardize",
    "soccerdata": "ingest",
    "statsbombpy": "ingest",
    "yaml": "core",
}


def require(module_name: str) -> ModuleType:
    """Importa un modulo opzionale o fallisce con un messaggio azionabile.

    Args:
        module_name: Nome importabile del modulo (per esempio ``"duckdb"``).

    Returns:
        Il modulo importato.

    Raises:
        MissingDependencyError: Se il modulo non è installato.

    Example:
        >>> duckdb = require("duckdb")  # doctest: +SKIP
    """
    try:
        return import_module(module_name)
    except ModuleNotFoundError as exc:
        extra = EXTRA_BY_MODULE.get(module_name.split(".")[0])
        if extra == "core":
            extra = None
        raise MissingDependencyError(module_name, extra) from exc


def has(module_name: str) -> bool:
    """Verifica se un modulo opzionale è importabile, senza sollevare eccezioni.

    Args:
        module_name: Nome importabile del modulo.

    Returns:
        ``True`` se il modulo è disponibile nell'ambiente corrente.

    Example:
        >>> has("duckdb")
        False
    """
    try:
        require(module_name)
    except MissingDependencyError:
        return False
    return True


def require_any(module_names: list[str]) -> ModuleType:
    """Importa il primo modulo disponibile fra quelli indicati.

    Utile per gli adapter che accettano più backend alternativi (per esempio
    ``statsbombpy`` oppure parsing JSON manuale).

    Args:
        module_names: Nomi importabili in ordine di preferenza.

    Returns:
        Il primo modulo disponibile.

    Raises:
        MissingDependencyError: Se nessuno dei moduli è installato.
    """
    for module_name in module_names:
        try:
            return import_module(module_name)
        except ModuleNotFoundError:
            continue
    extra = EXTRA_BY_MODULE.get(module_names[0].split(".")[0]) if module_names else None
    raise MissingDependencyError(" | ".join(module_names) or "<nessuno>", extra)


def missing(module_names: list[str]) -> list[str]:
    """Restituisce il sottoinsieme dei moduli non installati.

    Args:
        module_names: Nomi importabili da verificare.

    Returns:
        I nomi non disponibili, nell'ordine ricevuto.
    """
    return [name for name in module_names if not has(name)]


def as_table() -> dict[str, Any]:
    """Riepiloga la disponibilità delle dipendenze opzionali note.

    Returns:
        Dizionario ``{nome_modulo: {"installed": bool, "extra": str | None}}``.
    """
    return {
        name: {"installed": has(name), "extra": EXTRA_BY_MODULE.get(name)}
        for name in sorted(EXTRA_BY_MODULE)
    }
