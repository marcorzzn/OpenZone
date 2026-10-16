"""Modelli di possesso.

Il possesso è la variabile più mal definita dell'analisi calcistica: quasi tutte le
metriche di sequenza (key passes, xA, VAEP) dipendono dal sapere chi aveva il pallone e
quando la sequenza è finita, e ogni provider lo definisce a modo suo.

Questo modulo dovrà fornire una definizione operativa, esplicita e parametrica: una
sequenza di possesso è un insieme di eventi consecutivi della stessa squadra, che
termina quando l'avversario tocca il pallone o quando passa troppo tempo. Entrambi i
criteri sono argomenti, e la definizione usata viene registrata nel risultato.

Example:
    >>> from openzone.models import possession
    >>> possession.available()
    False
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

__all__ = ["DEFAULT_SEQUENCE_GAP_SECONDS", "available", "possession_sequences"]

#: Intervallo massimo, in secondi, fra due eventi della stessa squadra perché la
#: sequenza continui.
DEFAULT_SEQUENCE_GAP_SECONDS = 5.0


def available() -> bool:
    """Indica se i modelli di possesso sono implementati.

    Returns:
        Sempre ``False``: previsti in Fase 2.
    """
    return False


def possession_sequences(
    events: pd.DataFrame,
    *,
    gap_seconds: float = DEFAULT_SEQUENCE_GAP_SECONDS,
    **kwargs: Any,
) -> pd.DataFrame:
    """Segmenta gli eventi in sequenze di possesso.

    Args:
        events: Eventi standardizzati.
        gap_seconds: Intervallo massimo fra due eventi della stessa squadra.
        **kwargs: Criteri aggiuntivi di fine sequenza.

    Returns:
        Eventi con le colonne ``possession_id`` e ``possession_team_id``.

    Raises:
        NotImplementedError: Previsto in Fase 2: è il prerequisito di key passes, xA e
            VAEP, e va definito prima di quelle metriche.
    """
    _ = (events, gap_seconds, kwargs)
    raise NotImplementedError(
        "models.possession.possession_sequences: previsto in Fase 2. "
        "È il prerequisito di key passes, xA e VAEP."
    )
