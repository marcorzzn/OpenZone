"""Metriche di 1ª generazione: conteggi dagli eventi standardizzati.

Nessun modello, nessuna stima: solo filtri e raggruppamenti sugli eventi canonici.
Sono le metriche che tutti i provider concordano nel definire e che quindi non
richiedono avvertenze, tranne una: la base di calcolo. Il possesso è l'esempio
tipico, e per questo ogni funzione di possesso dichiara esplicitamente su cosa è
calcolato.

Le funzioni accettano un DataFrame conforme a
:data:`openzone.standardize.CANONICAL_EVENT_SCHEMA` e restituiscono o un sottoinsieme
di righe, o una Series aggregata, o un DataFrame aggregato.

Example:
    >>> from openzone.metrics import basic
    >>> shots = basic.shots(events)  # doctest: +SKIP
    >>> basic.shot_counts(events)  # doctest: +SKIP
"""

from __future__ import annotations

from typing import Any, Literal

import pandas as pd

from openzone.exceptions import OpenZoneError

__all__ = [
    "POSSESSION_BASES",
    "assists",
    "goals",
    "key_passes",
    "pass_completion",
    "possession",
    "shot_counts",
    "shots",
]

#: Basi di calcolo ammesse per il possesso. Dichiararle nel risultato è obbligatorio:
#: due possessi calcolati su basi diverse non sono confrontabili.
POSSESSION_BASES: tuple[str, ...] = ("events", "passes", "time")

#: Nome del tipo evento che identifica un gol nello schema canonico.
GOAL_TYPE_NAME = "Goal"

#: Famiglie considerate azioni di tiro.
_SHOT_FAMILY = "shot"


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], function: str) -> None:
    """Verifica che il DataFrame contenga le colonne necessarie.

    Args:
        frame: DataFrame da verificare.
        columns: Colonne richieste.
        function: Nome della funzione chiamante, usato nel messaggio di errore.

    Raises:
        OpenZoneError: Se mancano colonne.
    """
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise OpenZoneError(
            f"{function}: colonne mancanti {', '.join(missing)}. "
            "Gli eventi devono essere standardizzati prima del calcolo: "
            "usa openzone.standardize."
        )


def shots(events: pd.DataFrame) -> pd.DataFrame:
    """Restituisce i tiri presenti nella tabella eventi.

    Args:
        events: Eventi standardizzati.

    Returns:
        Le righe con famiglia ``shot``, con l'indice originale preservato.

    Raises:
        OpenZoneError: Se manca la colonna ``family``.

    Example:
        >>> len(shots(events))  # doctest: +SKIP
        24
    """
    _require_columns(events, ("family",), "basic.shots")
    return events.loc[events["family"] == _SHOT_FAMILY]


def goals(events: pd.DataFrame) -> pd.DataFrame:
    """Restituisce i gol presenti nella tabella eventi.

    Args:
        events: Eventi standardizzati.

    Returns:
        Le righe di tiro con ``type_name`` uguale a ``"Goal"``.

    Raises:
        OpenZoneError: Se mancano le colonne ``family`` o ``type_name``.
    """
    _require_columns(events, ("family", "type_name"), "basic.goals")
    stripped = events["type_name"].astype("string").str.strip()
    return events.loc[(events["family"] == _SHOT_FAMILY) & (stripped == GOAL_TYPE_NAME)]


def shot_counts(events: pd.DataFrame, by: str = "player_id") -> pd.DataFrame:
    """Conta tiri e gol per gruppo.

    Args:
        events: Eventi standardizzati.
        by: Colonna di raggruppamento (``"player_id"``, ``"team_id"``, ...).

    Returns:
        DataFrame con ``shots`` e ``goals`` per ciascun valore di ``by``, ordinato per
        numero di tiri decrescente.

    Raises:
        OpenZoneError: Se manca la colonna di raggruppamento o le colonne necessarie.
    """
    _require_columns(events, (by,), "basic.shot_counts")
    shot_rows = shots(events)
    goal_rows = goals(events)
    counts = pd.DataFrame(
        {
            "shots": shot_rows.groupby(by, observed=True).size(),
            "goals": goal_rows.groupby(by, observed=True).size(),
        }
    )
    counts["goals"] = counts["goals"].fillna(0).astype("int64")
    counts["shots"] = counts["shots"].fillna(0).astype("int64")
    counts["conversion"] = (counts["goals"] / counts["shots"].replace(0, pd.NA)).astype("Float64")
    return counts.sort_values(["shots", "goals"], ascending=False)


def pass_completion(events: pd.DataFrame, by: str = "team_id") -> pd.DataFrame:
    """Calcola passaggi tentati, completati e percentuale di riuscita.

    Args:
        events: Eventi standardizzati.
        by: Colonna di raggruppamento.

    Returns:
        DataFrame con ``passes``, ``completed`` e ``completion_pct``.

    Raises:
        OpenZoneError: Se mancano le colonne ``family`` o ``outcome``.
    """
    _require_columns(events, ("family", "outcome", by), "basic.pass_completion")
    passes = events.loc[events["family"] == "pass"]
    outcome = passes["outcome"].astype("boolean").fillna(False)
    grouped = passes.assign(_completed=outcome).groupby(by, observed=True)
    result = pd.DataFrame(
        {
            "passes": grouped.size(),
            "completed": grouped["_completed"].sum(),
        }
    )
    result["completion_pct"] = (
        100.0 * result["completed"] / result["passes"].replace(0, pd.NA)
    ).astype("Float64")
    return result.sort_values("passes", ascending=False)


def possession(
    events: pd.DataFrame,
    by: str = "team_id",
    basis: Literal["events", "passes", "time"] = "events",
) -> pd.DataFrame:
    """Calcola il possesso su una base di calcolo dichiarata.

    Args:
        events: Eventi standardizzati.
        by: Colonna di raggruppamento (tipicamente ``"team_id"``).
        basis: Base di calcolo.

            * ``"events"``: quota di eventi attribuiti alla squadra;
            * ``"passes"``: quota di passaggi tentati;
            * ``"time"``: quota di tempo fra il primo e l'ultimo evento della squadra,
              che approssima il possesso sul tempo effettivo.

    Returns:
        DataFrame con ``possession_pct`` e la base usata nella colonna ``basis``.

    Raises:
        OpenZoneError: Se la base non è ammessa o mancano le colonne necessarie.
        NotImplementedError: Se la base è ``"time"``: richiede la ricostruzione delle
            sequenze di possesso, prevista in Fase 2.
    """
    if basis not in POSSESSION_BASES:
        raise OpenZoneError(f"Base di possesso non valida: {basis!r}. Ammesse: {POSSESSION_BASES}")
    _require_columns(events, (by,), "basic.possession")

    if basis == "time":
        raise NotImplementedError(
            "basic.possession(basis='time'): il possesso sul tempo effettivo richiede "
            "la ricostruzione delle sequenze di possesso, prevista in Fase 2."
        )

    if basis == "events":
        counts = events.groupby(by, observed=True).size()
    else:
        _require_columns(events, ("family",), "basic.possession")
        counts = events.loc[events["family"] == "pass"].groupby(by, observed=True).size()

    total = int(counts.sum())
    result = pd.DataFrame({"count": counts})
    result["possession_pct"] = (
        100.0 * result["count"] / total if total else pd.Series(dtype="Float64")
    ).astype("Float64")
    result["basis"] = basis
    return result.sort_values("possession_pct", ascending=False)


def key_passes(events: pd.DataFrame, by: str = "player_id") -> pd.DataFrame:
    """Conta i passaggi che hanno generato un tiro.

    Args:
        events: Eventi standardizzati.
        by: Colonna di raggruppamento.

    Returns:
        DataFrame con ``key_passes`` per gruppo.

    Raises:
        NotImplementedError: La definizione operativa richiede la ricostruzione delle
            sequenze di possesso (cosa significa "stessa azione"), che è un parametro
            esplicito e non un dettaglio implementativo. Prevista in Fase 2.
    """
    _ = (events, by)
    raise NotImplementedError(
        "basic.key_passes: richiede la ricostruzione delle sequenze di possesso, "
        "prevista in Fase 2 (vedi OPENZONE_BLUEPRINT.md §8)."
    )


def assists(events: pd.DataFrame, by: str = "player_id") -> pd.DataFrame:
    """Conta gli assist secondo la definizione dichiarata.

    Args:
        events: Eventi standardizzati.
        by: Colonna di raggruppamento.

    Returns:
        DataFrame con ``assists`` per gruppo.

    Raises:
        NotImplementedError: Gli assist dipendono da qualificatori specifici della
            fonte, la cui mappatura è in Fase 1 e la cui verifica è in Fase 2. Nel
            frattempo questa funzione non indovina: fallisce.
    """
    _ = (events, by)
    raise NotImplementedError(
        "basic.assists: dipende dai qualificatori della fonte, da mappare e verificare "
        "in Fase 1-2 (vedi OPENZONE_BLUEPRINT.md §8)."
    )


def summary(events: pd.DataFrame) -> dict[str, Any]:
    """Riepilogo rapido dei conteggi principali.

    Args:
        events: Eventi standardizzati.

    Returns:
        Dizionario con numero di eventi, partite, squadre, tiri e gol.

    Example:
        >>> summary(events)["shots"]  # doctest: +SKIP
        24
    """
    return {
        "events": int(len(events)),
        "matches": int(events["match_id"].nunique()) if "match_id" in events else 0,
        "teams": int(events["team_id"].nunique()) if "team_id" in events else 0,
        "shots": int(len(shots(events))),
        "goals": int(len(goals(events))),
    }
