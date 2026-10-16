"""Adapter per ``soccerdata``: FBref, Understat, WhoScored, FotMob, Sofascore, ...

``soccerdata`` è una libreria che astrae molti siti sotto un'interfaccia comune
(``read_leagues``, ``read_schedule``, ``read_events``, ...) e restituisce DataFrame
con indici coerenti fra fonti. Questo adapter la incapsula in modo che OpenZone
dipenda da un solo punto, e che un cambio di API della libreria si risolva in un file.

Avvertenza sui termini di servizio: ``soccerdata`` effettua scraping. Che la libreria
lo renda comodo non lo rende permesso. Prima di usare una fonte, leggi la sua scheda
in ``glossary/sources.yaml``: per WhoScored e Sofascore i termini vietano l'accesso
programmatico, quindi quegli adapter non vanno usati in produzione.

Example:
    >>> from openzone.ingest import soccerdata
    >>> soccerdata.available()
    False
    >>> frame = soccerdata.load_matches("Serie A", "2024-2025")  # doctest: +SKIP
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from openzone._deps import has, require
from openzone.exceptions import SourceNotAvailableError

__all__ = [
    "SOCCERDATA_READERS",
    "available",
    "client",
    "load_events",
    "load_matches",
    "name",
    "reader",
    "requires",
]

#: Chiave della fonte, come in ``glossary/sources.yaml``.
name = "soccerdata"

#: Moduli opzionali richiesti.
requires: tuple[str, ...] = ("soccerdata",)

#: Nome della classe ``soccerdata`` per ciascuna fonte supportata.
SOCCERDATA_READERS: dict[str, str] = {
    "fbref": "FBref",
    "understat": "Understat",
    "whoscored": "WhoScored",
    "fotmob": "FotMob",
    "sofascore": "Sofascore",
    "sofifa": "SoFIFA",
    "espn": "ESPN",
    "clubelo": "ClubElo",
    "football_data_co_uk": "FootballData",
    "matchhistory": "MatchHistory",
}


def available() -> bool:
    """Indica se ``soccerdata`` è installato.

    Returns:
        ``True`` se la libreria è importabile.
    """
    return has("soccerdata")


def reader(source: str, *args: Any, **kwargs: Any) -> Any:
    """Istanzia il lettore ``soccerdata`` di una fonte.

    Args:
        source: Chiave della fonte, fra quelle in :data:`SOCCERDATA_READERS`.
        *args: Argomenti posizionali passati al costruttore (per esempio lega e
            stagione).
        **kwargs: Argomenti con nome passati al costruttore.

    Returns:
        Un'istanza del lettore ``soccerdata``.

    Raises:
        MissingDependencyError: Se ``soccerdata`` non è installato.
        KeyError: Se la fonte non è gestita da questo adapter.
    """
    if source not in SOCCERDATA_READERS:
        known = ", ".join(sorted(SOCCERDATA_READERS))
        raise KeyError(f"Fonte non gestita: {source!r}. Fonti note: {known}")
    module = require("soccerdata")
    return getattr(module, SOCCERDATA_READERS[source])(*args, **kwargs)


def client(source: str = "fbref", **kwargs: Any) -> Any:
    """Alias di :func:`reader`, con ``fbref`` come fonte predefinita.

    Args:
        source: Chiave della fonte.
        **kwargs: Argomenti passati al costruttore del lettore.

    Returns:
        Un'istanza del lettore ``soccerdata``.
    """
    return reader(source, **kwargs)


def load_matches(source: str = "fbref", *args: Any, **kwargs: Any) -> pd.DataFrame:
    """Legge il calendario di una competizione-stagione.

    Args:
        source: Chiave della fonte.
        *args: Argomenti passati al lettore.
        **kwargs: Argomenti passati al metodo ``read_schedule``.

    Returns:
        DataFrame del calendario, con l'indice ``soccerdata`` preservato.
    """
    return reader(source, *args).read_schedule(**kwargs)


def load_events(source: str = "whoscored", *args: Any, **kwargs: Any) -> pd.DataFrame:
    """Legge gli eventi di una partita.

    Args:
        source: Chiave della fonte. Non tutte le fonti espongono gli eventi: le
            uniche che lo fanno sono quelle basate su feed evento completi.
        *args: Argomenti passati al lettore.
        **kwargs: Argomenti passati al metodo ``read_events``.

    Returns:
        DataFrame degli eventi grezzi.

    Raises:
        SourceNotAvailableError: Se la fonte non espone gli eventi o la lettura
            fallisce per un motivo noto (partita assente, accesso negato).
    """
    instance = reader(source, *args)
    read_events = getattr(instance, "read_events", None)
    if read_events is None:
        raise SourceNotAvailableError(
            f"La fonte {source!r} non espone eventi: usa solo statistiche aggregate."
        )
    try:
        return read_events(**kwargs)
    except Exception as exc:  # noqa: BLE001 - la libreria solleva eccezioni proprie
        raise SourceNotAvailableError(
            f"Lettura eventi fallita per {source!r}: {exc}"
        ) from exc
