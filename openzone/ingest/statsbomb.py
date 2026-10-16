"""Adapter per StatsBomb Open Data.

Fonte di riferimento per i test di OpenZone: aperta, scaricabile in blocco, con
eventi ricchi di qualificatori. Contiene competizioni selezionate, fra cui la
Serie A 2015/16: è una sola stagione, quindi non basta per un'analisi storica.

Il repository espone file JSON statici, quindi l'accesso avviene con la libreria
standard (`urllib`) e non richiede né chiavi API né librerie di scraping: l'unica
dipendenza è ``pandas`` per la costruzione dei DataFrame.

Layout dei dati (``data/`` nel repository ``statsbomb/open-data``)::

    competitions.json
    matches/{competition_id}/{season_id}.json
    events/{match_id}.json
    lineups/{match_id}.json

Gli eventi sono annidati: ogni evento ha una sezione ``type``, ``player``, ``team``,
``location`` e una lista ``qualifiers``. Questo adapter appiattisce solo il primo
livello e conserva le strutture annidate come oggetti Python, lasciando la
normalizzazione a :mod:`openzone.standardize`.

Example:
    >>> from openzone.ingest import statsbomb
    >>> matches = statsbomb.load_matches(competition_id=12, season_id=27)  # doctest: +SKIP
    >>> events = statsbomb.load_events(3721143)  # doctest: +SKIP
"""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from openzone.exceptions import SourceNotAvailableError

__all__ = [
    "BASE_URL",
    "available",
    "competitions",
    "load_events",
    "load_lineups",
    "load_matches",
    "name",
    "requires",
]

#: Chiave della fonte, come in ``glossary/sources.yaml``.
name = "statsbomb_open_data"

#: Moduli opzionali richiesti (tutti core per questa fonte).
requires: tuple[str, ...] = ()

#: Radice dei file JSON nel repository pubblico.
BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"

#: Timeout predefinito delle richieste HTTP, in secondi.
DEFAULT_TIMEOUT = 30.0

#: Competizione e stagione usate dai test: Serie A 2015/16.
SERIE_A_COMPETITION_ID = 12
SERIE_A_SEASON_ID = 27


def available() -> bool:
    """Indica se l'adapter è utilizzabile.

    StatsBomb Open Data non richiede credenziali: l'adapter è sempre disponibile,
    salvo ``pandas`` mancante, che è una dipendenza core di OpenZone.

    Returns:
        Sempre ``True`` in un'installazione valida.
    """
    return True


def _fetch_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> Any:
    """Scarica e decodifica un file JSON.

    Args:
        url: URL assoluto del file JSON.
        timeout: Timeout della richiesta in secondi.

    Returns:
        Il contenuto JSON decodificato.

    Raises:
        SourceNotAvailableError: Se la richiesta fallisce, il server risponde con un
            errore HTTP, il corpo non è JSON valido o il timeout scade.
    """
    request = Request(
        url,
        headers={"User-Agent": "openzone/0.1 (+https://github.com/marcorzzn/OpenZone)"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL https costante
            payload = response.read()
    except HTTPError as exc:
        raise SourceNotAvailableError(
            f"StatsBomb Open Data ha risposto {exc.code} per {url}. "
            "Verifica l'identificativo richiesto: partita, competizione o stagione inesistente."
        ) from exc
    except URLError as exc:
        raise SourceNotAvailableError(
            f"StatsBomb Open Data non raggiungibile ({exc.reason}) per {url}. "
            "Serve una connessione di rete."
        ) from exc
    except TimeoutError as exc:
        raise SourceNotAvailableError(
            f"Timeout dopo {timeout}s su {url}. Riprova o aumenta il timeout."
        ) from exc
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SourceNotAvailableError(
            f"Risposta non JSON da {url}: il repository potrebbe essere cambiato."
        ) from exc


def competitions(timeout: float = DEFAULT_TIMEOUT) -> pd.DataFrame:
    """Elenca competizioni e stagioni disponibili.

    Args:
        timeout: Timeout della richiesta in secondi.

    Returns:
        DataFrame con una riga per competizione-stagione, con le colonne originali
        della fonte (``competition_id``, ``season_id``, ``competition_name``,
        ``season_name``, ``country_name``, ...).
    """
    raw = _fetch_json(f"{BASE_URL}/competitions.json", timeout=timeout)
    return pd.json_normalize(raw)


def load_matches(
    competition_id: int = SERIE_A_COMPETITION_ID,
    season_id: int = SERIE_A_SEASON_ID,
    timeout: float = DEFAULT_TIMEOUT,
) -> pd.DataFrame:
    """Restituisce le partite di una competizione-stagione.

    Args:
        competition_id: Identificativo della competizione (12 = Serie A).
        season_id: Identificativo della stagione (27 = 2015/16).
        timeout: Timeout della richiesta in secondi.

    Returns:
        DataFrame delle partite, con le colonne originali della fonte e le sezioni
        annidate (``home_team``, ``away_team``, ``competition``, ``season``)
        appiattite con prefisso.
    """
    raw = _fetch_json(f"{BASE_URL}/matches/{competition_id}/{season_id}.json", timeout=timeout)
    frame = pd.json_normalize(raw)
    return frame


def load_events(match_id: int, timeout: float = DEFAULT_TIMEOUT) -> pd.DataFrame:
    """Restituisce gli eventi grezzi di una partita.

    Args:
        match_id: Identificativo StatsBomb della partita.
        timeout: Timeout della richiesta in secondi.

    Returns:
        DataFrame con una riga per evento. Le colonne annidate (``type``,
        ``player``, ``team``, ``possession_team``, ``location``, ``qualifiers``)
        sono conservate come oggetti Python: la normalizzazione avviene in
        :mod:`openzone.standardize`.

    Raises:
        SourceNotAvailableError: Se la partita non esiste o la rete non risponde.
    """
    raw = _fetch_json(f"{BASE_URL}/events/{match_id}.json", timeout=timeout)
    return pd.DataFrame(raw)


def load_lineups(match_id: int, timeout: float = DEFAULT_TIMEOUT) -> pd.DataFrame:
    """Restituisce le formazioni di una partita.

    Args:
        match_id: Identificativo StatsBomb della partita.
        timeout: Timeout della richiesta in secondi.

    Returns:
        DataFrame con una riga per giocatore convocato, con le colonne originali
        della fonte.
    """
    raw = _fetch_json(f"{BASE_URL}/lineups/{match_id}.json", timeout=timeout)
    rows: list[dict[str, Any]] = []
    for team in raw:
        for player in team.get("lineup", []):
            rows.append(
                {
                    "team_id": team.get("team_id"),
                    "team_name": team.get("team_name"),
                    **player,
                }
            )
    return pd.DataFrame(rows)
