"""Mappe di tiro.

Il grafico più richiesto e il più facile da sbagliare: la dimensione dei pallini deve
codificare una sola cosa per volta (xG *oppure* numero di tiri, non entrambe), e il
titolo deve dire da quale modello viene l'xG mostrato.

Example:
    >>> from openzone.viz import shots
    >>> shots.available()
    False
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openzone._deps import has

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

__all__ = ["available", "shot_map"]

#: Colori predefiniti: gol, tiro parato, tiro fuori.
DEFAULT_COLOURS = ("#1a9850", "#f46d43", "#bdbdbd")


def available() -> bool:
    """Indica se le dipendenze della mappa di tiro sono installate.

    Returns:
        ``True`` se ``mplsoccer`` è importabile.
    """
    return has("mplsoccer")


def shot_map(
    shots: pd.DataFrame,
    *,
    size_by: str | None = "xg",
    colour_by: str | None = "outcome",
    model_label: str | None = None,
    **kwargs: Any,
) -> Any:
    """Disegna una mappa di tiro.

    Args:
        shots: Tabella dei tiri standardizzati.
        size_by: Colonna usata per la dimensione dei pallini. ``None`` per dimensione
            costante.
        colour_by: Colonna usata per il colore.
        model_label: Etichetta del modello che ha prodotto l'xG mostrato, riportata nel
            titolo. Se ``size_by`` è un xG e l'etichetta manca, la funzione solleva un
            errore: un xG senza provenienza non va in un grafico.
        **kwargs: Argomenti passati a ``mplsoccer``.

    Returns:
        Coppia ``(figura, asse)``.

    Raises:
        MissingDependencyError: Se ``mplsoccer`` non è installato.
        OpenZoneError: Se si disegna un xG senza dichiararne il modello.
        NotImplementedError: Previsto in Fase 4.
    """
    from openzone._deps import require
    from openzone.exceptions import OpenZoneError

    if size_by is not None and "xg" in size_by.lower() and not model_label:
        raise OpenZoneError(
            "shot_map: mostrare un xG senza dichiarare il modello che l'ha prodotto "
            "rende il grafico inutilizzabile. Passa model_label."
        )
    require("mplsoccer")
    _ = (shots, colour_by, kwargs)
    raise NotImplementedError("viz.shots.shot_map: previsto in Fase 4.")
