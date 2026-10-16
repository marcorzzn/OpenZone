"""Reti di passaggio e frecce.

Il grafico che rende visibile la struttura di una squadra: nodi sui giocatori, archi
pesati sui passaggi. Le regole che rendono leggibile una rete:

* normalizzare i pesi per i minuti giocati, altrimenti il grafico mostra chi è rimasto
  in campo più a lungo;
* mostrare la direzione del gioco con una freccia o una nota, perché la stessa rete
  letta al contrario racconta un'altra storia;
* non disegnare più di venti archi: oltre, il grafico diventa una ragnatela e non
  comunica più nulla.

Example:
    >>> from openzone.viz import passes
    >>> passes.available()
    False
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openzone._deps import has

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

__all__ = ["MAX_EDGES", "available", "pass_network", "pass_arrows"]

#: Numero massimo di archi disegnati in una rete di passaggio.
MAX_EDGES = 20


def available() -> bool:
    """Indica se le dipendenze della rete di passaggio sono installate.

    Args:
        Nessuno.

    Returns:
        ``True`` se ``mplsoccer`` è importabile.
    """
    return has("mplsoccer")


def pass_arrows(
    events: pd.DataFrame,
    *,
    team_id: Any | None = None,
    **kwargs: Any,
) -> Any:
    """Disegna i passaggi come frecce da partenza ad arrivo.

    Args:
        events: Eventi standardizzati.
        team_id: Se indicato, limita il grafico a una squadra.
        **kwargs: Argomenti passati a ``mplsoccer``.

    Returns:
        Coppia ``(figura, asse)``.

    Raises:
        MissingDependencyError: Se ``mplsoccer`` non è installato.
        NotImplementedError: Previsto in Fase 4.
    """
    from openzone._deps import require

    require("mplsoccer")
    _ = (events, team_id, kwargs)
    raise NotImplementedError("viz.passes.pass_arrows: previsto in Fase 4.")


def pass_network(
    edges: pd.DataFrame,
    positions: pd.DataFrame,
    *,
    max_edges: int = MAX_EDGES,
    **kwargs: Any,
) -> Any:
    """Disegna una rete di passaggio.

    Args:
        edges: Archi prodotti da
            :func:`openzone.spatial.pass_networks.pass_edges`.
        positions: Posizione media di ogni giocatore, con le colonne ``player_id``,
            ``x`` e ``y``.
        max_edges: Numero massimo di archi da disegnare.
        **kwargs: Argomenti passati a ``mplsoccer``.

    Returns:
        Coppia ``(figura, asse)``.

    Raises:
        MissingDependencyError: Se ``mplsoccer`` non è installato.
        NotImplementedError: Previsto in Fase 4.
    """
    from openzone._deps import require

    require("mplsoccer")
    _ = (edges, positions, max_edges, kwargs)
    raise NotImplementedError("viz.passes.pass_network: previsto in Fase 4.")
