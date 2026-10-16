"""OpenZone – motore Python per dati calcistici.

OpenZone trasforma dati grezzi ed eterogenei (Opta, StatsBomb, Understat, FBref,
WhoScored, ...) in dataset puliti, standardizzati e arricchiti con metriche avanzate.

La libreria è pensata per essere importata da applicazioni esterne (per esempio il
cruscotto OpenPitch) e non conosce nulla di esse: la dipendenza è unidirezionale.

Gli import pesanti sono pigri. ``import openzone`` non richiede ``pandas``,
``duckdb``, ``mplsoccer`` o alcuna libreria di scraping: solo ``PyYAML`` serve per
il glossario, e viene richiesto nel momento in cui lo si interroga.

Example:
    >>> import openzone
    >>> openzone.__version__
    '0.1.0'
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openzone.exceptions import (
    MissingDependencyError,
    OpenZoneError,
    SourceNotAvailableError,
)

if TYPE_CHECKING:  # pragma: no cover
    from openzone.api import (
        compute_xg,
        get_glossary,
        load_events,
        load_shots,
    )

__version__ = "0.1.0"

__all__ = [
    "MissingDependencyError",
    "OpenZoneError",
    "SourceNotAvailableError",
    "__version__",
    "compute_xg",
    "get_glossary",
    "load_events",
    "load_shots",
]

#: Nomi pubblici serviti pigramente da :mod:`openzone.api`.
_API_EXPORTS = frozenset({"compute_xg", "get_glossary", "load_events", "load_shots"})


def __getattr__(name: str) -> Any:
    """Risolve i nomi dell'API pubblica senza importare ``pandas`` a priori.

    Args:
        name: Attributo richiesto sul modulo.

    Returns:
        L'attributo corrispondente di :mod:`openzone.api`.

    Raises:
        AttributeError: Se il nome non fa parte della superficie pubblica.
    """
    if name in _API_EXPORTS:
        from openzone import api

        return getattr(api, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Elenca gli attributi del modulo, inclusi quelli pigri."""
    return sorted({*globals(), *_API_EXPORTS})
