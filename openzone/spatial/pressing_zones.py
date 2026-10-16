"""Zone di pressing e PPDA per zona.

Un PPDA unico per partita nasconde il fatto che il pressing non è uniforme: una squadra
può pressare altissimo su una fascia e aspettare al centro. Qui il campo viene diviso in
fasce lungo l'asse x e il PPDA viene calcolato per ciascuna, riusando
:func:`openzone.metrics.predictive.compute_ppda` con la stessa definizione di zona di
pressing: una sola implementazione, un solo significato.

Attenzione al campione: il PPDA di una singola fascia su una singola partita è calcolato
su poche decine di eventi, quindi rumoroso. Va aggregato su più partite prima di trarre
conclusioni, e il conteggio degli eventi va riportato accanto al valore.

Example:
    >>> from openzone.spatial import pressing_zones
    >>> table = pressing_zones.ppda_by_band(events, team_id=1)  # doctest: +SKIP
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from openzone.exceptions import OpenZoneError
from openzone.metrics.predictive import (
    DEFAULT_PRESSING_HEIGHT,
    PPDAResult,
    compute_ppda,
)

__all__ = [
    "DEFAULT_BANDS",
    "band_labels",
    "ppda_by_band",
    "ppda_table",
]

#: Fasce predefinite lungo l'asse x: dalla propria porta a quella avversaria.
DEFAULT_BANDS: tuple[tuple[float, float], ...] = (
    (0.0, 40.0),
    (40.0, 60.0),
    (60.0, 80.0),
    (80.0, 100.0),
)


def band_labels(bands: tuple[tuple[float, float], ...] = DEFAULT_BANDS) -> list[str]:
    """Genera le etichette delle fasce.

    Args:
        bands: Fasce come coppie ``(x_min, x_max)``.

    Returns:
        Etichette nella forma ``"60-80"``.

    Example:
        >>> band_labels()[0]
        '0-40'
    """
    return [f"{int(low)}-{int(high)}" for low, high in bands]


def ppda_by_band(
    events: pd.DataFrame,
    team_id: Any,
    *,
    bands: tuple[tuple[float, float], ...] = DEFAULT_BANDS,
    action_families: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Calcola il PPDA di una squadra per ciascuna fascia di campo.

    La zona di pressing di ciascuna fascia è la fascia stessa: si contano i passaggi
    avversari e le azioni difensive che avvengono dentro i suoi limiti.

    Args:
        events: Eventi standardizzati.
        team_id: Squadra di cui calcolare il PPDA.
        bands: Fasce di campo come coppie ``(x_min, x_max)``.
        action_families: Famiglie contate come azione difensiva; se omesso si usa il
            valore predefinito di :func:`openzone.metrics.predictive.compute_ppda`.

    Returns:
        DataFrame con una riga per fascia e le colonne ``band``, ``x_min``, ``x_max``,
        ``ppda``, ``opponent_passes`` e ``defensive_actions``.

    Raises:
        OpenZoneError: Se mancano le colonne necessarie.

    Example:
        >>> table = ppda_by_band(events, team_id=1)  # doctest: +SKIP
    """
    for column in ("team_id", "family", "x"):
        if column not in events.columns:
            raise OpenZoneError(f"pressing_zones.ppda_by_band: colonna mancante {column!r}")

    rows: list[dict[str, Any]] = []
    for low, high in bands:
        inside = events.loc[(events["x"] >= low) & (events["x"] < high)]
        kwargs: dict[str, Any] = {"pressing_height": 1.0}
        if action_families is not None:
            kwargs["action_families"] = action_families
        result: PPDAResult = compute_ppda(inside, team_id, **kwargs)
        rows.append(
            {
                "band": f"{int(low)}-{int(high)}",
                "x_min": low,
                "x_max": high,
                "ppda": result.value,
                "opponent_passes": result.opponent_passes,
                "defensive_actions": result.defensive_actions,
                "events": int(len(inside)),
            }
        )
    return pd.DataFrame(rows)


def ppda_table(
    events: pd.DataFrame,
    *,
    bands: tuple[tuple[float, float], ...] = DEFAULT_BANDS,
    pressing_height: float = DEFAULT_PRESSING_HEIGHT,
) -> pd.DataFrame:
    """Calcola il PPDA partita per partita e per fascia, per ogni squadra presente.

    Args:
        events: Eventi standardizzati, anche di più partite.
        bands: Fasce di campo.
        pressing_height: Quota di campo usata per il PPDA complessivo di partita.

    Returns:
        DataFrame con una riga per ``(match_id, team_id, band)``, più la riga
        ``band="match"`` con il PPDA complessivo.

    Raises:
        OpenZoneError: Se manca la colonna ``match_id``.
    """
    if "match_id" not in events.columns:
        raise OpenZoneError("pressing_zones.ppda_table: colonna 'match_id' assente")

    rows: list[dict[str, Any]] = []
    for match_id, match_events in events.groupby("match_id", observed=True):
        for team_id in match_events["team_id"].dropna().unique():
            overall = compute_ppda(match_events, team_id, pressing_height=pressing_height)
            rows.append(
                {
                    "match_id": match_id,
                    "team_id": team_id,
                    "band": "match",
                    "ppda": overall.value,
                    "opponent_passes": overall.opponent_passes,
                    "defensive_actions": overall.defensive_actions,
                    "events": int(len(match_events)),
                }
            )
            for _, band_row in ppda_by_band(match_events, team_id, bands=bands).iterrows():
                rows.append(
                    {
                        "match_id": match_id,
                        "team_id": team_id,
                        "band": band_row["band"],
                        "ppda": band_row["ppda"],
                        "opponent_passes": band_row["opponent_passes"],
                        "defensive_actions": band_row["defensive_actions"],
                        "events": band_row["events"],
                    }
                )
    return pd.DataFrame(rows)
