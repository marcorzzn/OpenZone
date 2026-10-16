"""Adapter per l'API di football-data.org: calendari, risultati, classifiche.

Serve a completare i metadati di partita (data, competizione, squadre) che spesso
mancano nei dataset di eventi, e a verificare che i risultati combacino con quelli
ricostruiti dagli eventi: è un controllo incrociato utile prima di pubblicare un
report.

La chiave API viene letta dalla variabile d'ambiente ``FOOTBALL_DATA_ORG_TOKEN`` e
non viene mai scritta su disco né inclusa in un DataFrame, in un log o in un
messaggio di errore. Il piano gratuito ha una quota di richieste ridotta: le
funzioni accettano un timeout e falliscono con un errore esplicito quando la quota
è esaurita, invece di ritentare in silenzio.

Example:
    >>> from openzone.ingest import football_data_org
    >>> frame = football_data_org.load_matches("SA", season=2024)  # doctest: +SKIP
"""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

from openzone._deps import has, require
from openzone.exceptions import SourceNotAvailableError

__all__ = [
    "API_BASE",
    "TOKEN_ENV_VAR",
    "available",
    "competition_matches",
    "load_matches",
    "name",
    "requires",
    "standings",
]

#: Chiave della fonte, come in ``glossary/sources.yaml``.
name = "football_data_org"

#: Moduli opzionali richiesti.
requires: tuple[str, ...] = ("requests",)

#: Variabile d'ambiente che contiene la chiave API.
TOKEN_ENV_VAR = "FOOTBALL_DATA_ORG_TOKEN"

#: Radice dell'API v4.
API_BASE = "https://api.football-data.org/v4"

#: Timeout predefinito delle richieste, in secondi.
DEFAULT_TIMEOUT = 20.0


def _token() -> str:
    """Legge la chiave API dall'ambiente.

    Returns:
        La chiave API.

    Raises:
        SourceNotAvailableError: Se la variabile d'ambiente non è impostata.
    """
    token = os.environ.get(TOKEN_ENV_VAR, "").strip()
    if not token:
        raise SourceNotAvailableError(
            f"Chiave API assente: imposta la variabile d'ambiente {TOKEN_ENV_VAR}. "
            "OpenZone non salva mai la chiave su disco."
        )
    return token


def available() -> bool:
    """Indica se l'adapter è utilizzabile.

    Verifica la presenza di ``requests`` e della chiave API, senza contattare il
    servizio.

    Returns:
        ``True`` se la libreria è installata e la chiave è presente.
    """
    return has("requests") and bool(os.environ.get(TOKEN_ENV_VAR, "").strip())


def _get(path: str, params: dict[str, Any] | None = None, timeout: float = DEFAULT_TIMEOUT) -> Any:
    """Esegue una richiesta GET autenticata all'API.

    Args:
        path: Percorso relativo, per esempio ``"/competitions/SA/matches"``.
        params: Parametri di query.
        timeout: Timeout della richiesta in secondi.

    Returns:
        Il corpo JSON decodificato.

    Raises:
        SourceNotAvailableError: Se la quota è esaurita, la risorsa non esiste, la
            rete non risponde o il corpo non è JSON.
    """
    requests = require("requests")
    url = f"{API_BASE}{path}"
    try:
        response = requests.get(
            url,
            params=params,
            headers={"X-Auth-Token": _token()},
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001 - requests solleva eccezioni proprie
        raise SourceNotAvailableError(f"football-data.org non raggiungibile: {exc}") from exc

    if response.status_code == 429:
        raise SourceNotAvailableError(
            "Quota di richieste esaurita su football-data.org. "
            "Il piano gratuito consente un numero limitato di chiamate al minuto."
        )
    if response.status_code == 403:
        raise SourceNotAvailableError(
            "Chiave API rifiutata da football-data.org: verifica il valore di "
            f"{TOKEN_ENV_VAR} e i permessi del tuo piano."
        )
    if response.status_code >= 400:
        raise SourceNotAvailableError(
            f"football-data.org ha risposto {response.status_code} per {path}."
        )
    try:
        return response.json()
    except ValueError as exc:
        raise SourceNotAvailableError(f"Risposta non JSON da {path}.") from exc


def competition_matches(
    competition: str = "SA",
    season: int | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> pd.DataFrame:
    """Restituisce le partite di una competizione.

    Args:
        competition: Codice competizione (``"SA"`` per la Serie A).
        season: Anno di inizio della stagione; se omesso, la stagione corrente.
        timeout: Timeout della richiesta in secondi.

    Returns:
        DataFrame delle partite, con le colonne originali della fonte.
    """
    params: dict[str, Any] = {}
    if season is not None:
        params["season"] = season
    payload = _get(f"/competitions/{competition}/matches", params or None, timeout)
    return pd.json_normalize(payload.get("matches", []))


def load_matches(
    competition: str = "SA",
    season: int | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> pd.DataFrame:
    """Alias di :func:`competition_matches`.

    Args:
        competition: Codice competizione.
        season: Anno di inizio della stagione.
        timeout: Timeout della richiesta in secondi.

    Returns:
        DataFrame delle partite.
    """
    return competition_matches(competition, season, timeout)


def standings(
    competition: str = "SA",
    season: int | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> pd.DataFrame:
    """Restituisce la classifica di una competizione.

    Args:
        competition: Codice competizione.
        season: Anno di inizio della stagione.
        timeout: Timeout della richiesta in secondi.

    Returns:
        DataFrame con una riga per squadra.
    """
    params: dict[str, Any] = {}
    if season is not None:
        params["season"] = season
    payload = _get(f"/competitions/{competition}/standings", params or None, timeout)
    rows: list[dict[str, Any]] = []
    for block in payload.get("standings", []):
        for row in block.get("table", []):
            rows.append({"stage": block.get("stage"), "type": block.get("type"), **row})
    return pd.DataFrame(rows)
