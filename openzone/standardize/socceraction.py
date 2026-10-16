"""Conversione degli eventi in SPADL tramite ``socceraction``.

SPADL (Soccer Player Action Description Language) è un formato di azioni con una
grammatica rigida: ogni azione ha un tipo, un esito e coordinate di partenza e di
arrivo. È il prerequisito per VAEP e per l'xT basato su azioni, perché entrambi
richiedono sequenze di azioni confrontabili.

La conversione è un punto delicato: pretende uno stadio iniziale e finale per ogni
azione e un esito binario. Le fonti che non forniscono le coordinate di arrivo (per
esempio alcuni feed senza qualificatore di posizione finale) non sono convertibili
senza inventare dati. In quel caso la conversione fallisce con un errore esplicito:
meglio nessun VAEP che un VAEP costruito su coordinate inventate.

Example:
    >>> from openzone.standardize import socceraction
    >>> socceraction.available()
    False
    >>> spadl = socceraction.to_spadl(events_frame, provider="statsbomb")  # doctest: +SKIP
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openzone._deps import has, require

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

__all__ = ["SPADL_COLUMNS", "available", "to_actions", "to_spadl"]

#: Colonne dello schema SPADL.
SPADL_COLUMNS: tuple[str, ...] = (
    "game_id",
    "original_event_id",
    "action_id",
    "period_id",
    "time_seconds",
    "team_id",
    "player_id",
    "start_x",
    "start_y",
    "end_x",
    "end_y",
    "bodypart_id",
    "type_id",
    "result_id",
)


def available() -> bool:
    """Indica se ``socceraction`` è installato e può convertire gli eventi.

    ``socceraction`` richiede anche ``pandas``; entrambe le condizioni sono verificate
    qui.

    Returns:
        ``True`` se la libreria è importabile.
    """
    return has("socceraction")


def spadl_converters() -> dict[str, str]:
    """Elenca le funzioni di conversione SPADL disponibili per provider.

    Returns:
        Mappa ``{provider: percorso_qualificato_della_funzione}``.

    Raises:
        MissingDependencyError: Se ``socceraction`` non è installato.
    """
    require("socceraction")
    return {
        "opta": "socceraction.spadl.opta.convert_to_actions",
        "statsbomb": "socceraction.spadl.statsbomb.convert_to_actions",
        "wyscout": "socceraction.spadl.wyscout.convert_to_actions",
        "wyscout_v2": "socceraction.spadl.wyscout.convert_to_actions",
    }


def to_actions(
    events: pd.DataFrame,
    provider: str,
    *,
    home_team_id: Any,
    away_team_id: Any,
) -> pd.DataFrame:
    """Converte gli eventi grezzi in azioni SPADL.

    Args:
        events: DataFrame di eventi grezzi della fonte.
        provider: Chiave del provider (``"statsbomb"``, ``"opta"``, ``"wyscout"``).
        home_team_id: Identificativo della squadra di casa, necessario a SPADL per
            orientare le azioni.
        away_team_id: Identificativo della squadra ospite.

    Returns:
        DataFrame di azioni con le colonne :data:`SPADL_COLUMNS`.

    Raises:
        NotImplementedError: Il collegamento a ``socceraction`` è previsto in Fase 2
            della roadmap.
    """
    if not available():
        require("socceraction")
    if provider not in spadl_converters():
        known = ", ".join(sorted(spadl_converters()))
        raise KeyError(f"Provider non supportato per SPADL: {provider!r}. Noti: {known}")
    raise NotImplementedError(
        f"openzone.standardize.socceraction.to_actions: conversione {provider!r} "
        "prevista in Fase 2 (vedi OPENZONE_BLUEPRINT.md §8)."
    )


def to_spadl(events: pd.DataFrame, provider: str, **kwargs: Any) -> pd.DataFrame:
    """Alias di :func:`to_actions`.

    Args:
        events: DataFrame di eventi grezzi.
        provider: Chiave del provider.
        **kwargs: Argomenti passati a :func:`to_actions`.

    Returns:
        DataFrame di azioni SPADL.
    """
    return to_actions(events, provider, **kwargs)
