"""Adapter per WhoScored: eventi con descrizioni testuali.

WhoScored espone feed evento in stile Opta con descrizioni testuali di ogni azione:
è utile per capire il contesto di un evento quando un qualificatore numerico non è
sufficiente.

**Avvertenza.** I termini di servizio di WhoScored vietano lo scraping. L'adapter è
presente per due motivi legittimi: usare dati già ottenuti legalmente dall'utente, e
leggere i campioni che la fonte stessa pubblica per uso aperto. Non è un invito allo
scraping e non va abilitato in produzione: OpenZone non include dati WhoScored.

Example:
    >>> from openzone.ingest import whoscored
    >>> events = whoscored.load_events("Serie A", "2024-2025", "Match")  # doctest: +SKIP
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from openzone.ingest import soccerdata

__all__ = ["TOS_WARNING", "available", "load_events", "load_matches", "name", "requires"]

#: Chiave della fonte, come in ``glossary/sources.yaml``.
name = "whoscored"

#: Moduli opzionali richiesti.
requires: tuple[str, ...] = ("soccerdata",)

#: Avvertenza da mostrare quando si usa questa fonte.
TOS_WARNING = (
    "WhoScored vieta lo scraping nei propri termini di servizio. "
    "Usa questo adapter solo su dati ottenuti legalmente, mai in produzione."
)


def available() -> bool:
    """Indica se l'adapter è utilizzabile.

    Returns:
        ``True`` se ``soccerdata`` è installato.
    """
    return soccerdata.available()


def load_matches(league: str, season: str | int, **kwargs: Any) -> pd.DataFrame:
    """Legge il calendario di una competizione-stagione.

    Args:
        league: Nome della competizione (es. ``"Serie A"``).
        season: Stagione (es. ``"2024-2025"``).
        **kwargs: Argomenti aggiuntivi per ``read_schedule``.

    Returns:
        DataFrame del calendario.
    """
    return soccerdata.load_matches("whoscored", league, season, **kwargs)


def load_events(league: str, season: str | int, match_id: Any, **kwargs: Any) -> pd.DataFrame:
    """Legge gli eventi di una partita, incluse le descrizioni testuali.

    Args:
        league: Nome della competizione.
        season: Stagione.
        match_id: Identificativo della partita nella fonte.
        **kwargs: Argomenti aggiuntivi passati alla lettura.

    Returns:
        DataFrame degli eventi grezzi, con descrizioni testuali.
    """
    return soccerdata.load_events("whoscored", league, season, match_id=match_id, **kwargs)
