"""Metriche di 2ª generazione: qualità del singolo evento.

Qui ogni numero dipende da un modello. La conseguenza pratica è che due xG non sono
la stessa cosa, e che pubblicare un xG senza dire da quale modello viene lo rende
inutilizzabile: nessuno può confrontarlo con niente.

Per questo OpenZone tiene separati due valori che sembrano uguali e non lo sono:

* **xG della fonte** (:func:`source_xg`) — il valore calcolato da Opta, Understat o
  StatsBomb e fornito insieme all'evento. Serve al confronto e alla validazione.
* **xG di OpenZone** (:func:`compute_xg`) — il valore calcolato da un modello addestrato
  localmente, con il proprio training set e la propria validazione.

Nel DataFrame i due valori finiscono in colonne diverse, con nomi diversi. Sommarli o
sovrascriverne uno con l'altro è l'errore che questa separazione esiste per impedire.

Example:
    >>> from openzone.metrics import advanced
    >>> advanced.source_xg(shots)  # doctest: +SKIP
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from openzone.exceptions import OpenZoneError

__all__ = [
    "SOURCE_XG_COLUMNS",
    "big_chances",
    "compute_xa",
    "compute_xg",
    "compute_xgot",
    "source_xg",
]

#: Nomi di colonna in cui le fonti depositano il proprio xG, in ordine di preferenza.
SOURCE_XG_COLUMNS: tuple[str, ...] = (
    "xg",
    "xG",
    "shot_statsbomb_xg",
    "expected_goals",
    "expectedGoals",
)


def source_xg(shots: pd.DataFrame, column: str | None = None) -> pd.Series:
    """Estrae l'xG fornito dalla fonte.

    Args:
        shots: Tabella dei tiri, con una colonna di xG della fonte.
        column: Nome esplicito della colonna da usare. Se omesso, si cerca fra i nomi
            in :data:`SOURCE_XG_COLUMNS`.

    Returns:
        Serie con l'xG della fonte, allineata all'indice di ``shots``.

    Raises:
        OpenZoneError: Se nessuna colonna di xG è presente. In quel caso non si
            inventa un valore: la fonte semplicemente non lo fornisce.

    Example:
        >>> xg = source_xg(shots)  # doctest: +SKIP
        >>> float(xg.sum())  # doctest: +SKIP
        1.87
    """
    if column is not None:
        if column not in shots.columns:
            raise OpenZoneError(f"Colonna xG richiesta ma assente: {column!r}")
        return shots[column].astype("float64")

    for candidate in SOURCE_XG_COLUMNS:
        if candidate in shots.columns:
            return shots[candidate].astype("float64")

    raise OpenZoneError(
        "Nessuna colonna di xG della fonte trovata. Cercate: "
        f"{', '.join(SOURCE_XG_COLUMNS)}. "
        "Se la fonte non fornisce xG, usa compute_xg con un modello addestrato."
    )


def compute_xg(shots: pd.DataFrame, model: Any | None = None, **features: Any) -> pd.Series:
    """Calcola l'xG con il modello di OpenZone.

    Args:
        shots: Tabella dei tiri standardizzati.
        model: Modello addestrato da usare. Se omesso, si usa il modello distribuito
            con OpenZone, quando esisterà.
        **features: Feature aggiuntive richieste dal modello (pressione, parte del
            corpo, tipo di azione).

    Returns:
        Serie con l'xG calcolato, allineata all'indice di ``shots``.

    Raises:
        OpenZoneError: Se mancano le colonne necessarie al modello.
        NotImplementedError: Il modello non è ancora implementato: è previsto in
            Fase 2, insieme alla validazione out-of-sample.
    """
    _ = (shots, model, features)
    raise NotImplementedError(
        "advanced.compute_xg: modello xG previsto in Fase 2, con validazione "
        "out-of-sample (vedi OPENZONE_BLUEPRINT.md §8)."
    )


def compute_xa(passes: pd.DataFrame, **kwargs: Any) -> pd.Series:
    """Calcola l'xA: somma degli xG dei tiri generati dai passaggi.

    Args:
        passes: Tabella dei passaggi standardizzati, collegata ai tiri generati.
        **kwargs: Argomenti aggiuntivi (modello xG da usare, definizione di sequenza).

    Returns:
        Serie con l'xA per passaggio.

    Raises:
        NotImplementedError: Richiede prima :func:`compute_xg` e la ricostruzione
            delle sequenze di possesso. Prevista in Fase 2.
    """
    _ = (passes, kwargs)
    raise NotImplementedError(
        "advanced.compute_xa: dipende dal modello xG e dalle sequenze di possesso, "
        "previsti in Fase 2."
    )


def compute_xgot(shots: pd.DataFrame, **kwargs: Any) -> pd.Series:
    """Calcola l'xGOT: xG condizionato al tiro nello specchio.

    Args:
        shots: Tabella dei tiri, con le coordinate del pallone all'ingresso in porta.
        **kwargs: Argomenti aggiuntivi.

    Returns:
        Serie con l'xGOT per tiro.

    Raises:
        OpenZoneError: Se mancano le coordinate post-shot, che è il caso normale per
            le fonti evento: Understat e StatsBomb Open Data non le espongono.
        NotImplementedError: Il modello non è ancora implementato.
    """
    post_shot_columns = ("shot_end_x", "shot_end_y", "goalmouth_y", "goalmouth_z")
    if not any(column in shots.columns for column in post_shot_columns):
        raise OpenZoneError(
            "xGOT non calcolabile: mancano le coordinate del pallone all'ingresso in "
            f"porta (attese fra {', '.join(post_shot_columns)}). "
            "Le fonti evento standard non espongono dati post-shot: senza di essi "
            "l'xGOT non esiste, e un valore approssimato sarebbe peggio di nessun valore."
        )
    raise NotImplementedError("advanced.compute_xgot: modello previsto in Fase 2.")


def big_chances(shots: pd.DataFrame, **criteria: Any) -> pd.DataFrame:
    """Individua le occasioni chiare secondo criteri dichiarati.

    Args:
        shots: Tabella dei tiri standardizzati.
        **criteria: Soglie dei criteri (distanza massima, porta libera, uno contro uno).

    Returns:
        Le righe di ``shots`` classificate come occasioni chiare, con la colonna
        ``big_chance`` a ``True``.

    Raises:
        NotImplementedError: La classificazione è euristica e va definita e documentata
            prima di essere calcolata: prevista in Fase 2.
    """
    _ = (shots, criteria)
    raise NotImplementedError(
        "advanced.big_chances: criteri euristici da definire e documentare in Fase 2. "
        "La definizione del provider non è pubblica in dettaglio: una "
        "reimplementazione può solo approssimarla."
    )
