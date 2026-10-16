"""Adapter per Understat: xG per singolo tiro.

Understat è utile perché pubblica un xG indipendente per tiro: permette di
confrontare il modello di OpenZone con un valore esterno senza dover addestrare
nulla. Non pubblica i passaggi, quindi non basta per metriche di progressione,
possesso o pressing.

L'accesso avviene tramite ``soccerdata``: questo modulo esiste per esporre solo le
due operazioni sensate su questa fonte e per documentarne i limiti.

Example:
    >>> from openzone.ingest import understat
    >>> shots = understat.load_shots("Serie A", "2024")  # doctest: +SKIP
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from openzone.ingest import soccerdata

__all__ = ["available", "load_matches", "load_shots", "name", "requires"]

#: Chiave della fonte, come in ``glossary/sources.yaml``.
name = "understat"

#: Moduli opzionali richiesti.
requires: tuple[str, ...] = ("soccerdata",)


def available() -> bool:
    """Indica se l'adapter è utilizzabile.

    Returns:
        ``True`` se ``soccerdata`` è installato.
    """
    return soccerdata.available()


def load_matches(league: str, season: str | int, **kwargs: Any) -> pd.DataFrame:
    """Legge il calendario di una competizione-stagione.

    Args:
        league: Nome della competizione nel formato di ``soccerdata`` (es. ``"Serie A"``).
        season: Stagione nel formato di ``soccerdata`` (es. ``"2024"``).
        **kwargs: Argomenti aggiuntivi per ``read_schedule``.

    Returns:
        DataFrame del calendario.
    """
    return soccerdata.load_matches("understat", league, season, **kwargs)


def load_shots(league: str, season: str | int, **kwargs: Any) -> pd.DataFrame:
    """Legge gli eventi di tiro con il valore xG della fonte.

    Args:
        league: Nome della competizione.
        season: Stagione.
        **kwargs: Argomenti aggiuntivi passati alla lettura della partita.

    Returns:
        DataFrame dei tiri, con coordinate e xG fornito dalla fonte.
    """
    return soccerdata.load_events("understat", league, season, **kwargs)
