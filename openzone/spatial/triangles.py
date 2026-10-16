"""Triangoli di passaggio.

Un triangolo è una terna di giocatori che si sono passati la palla a vicenda in tutti e
tre i versi: è un indicatore di fluidità del gioco, perché mostra combinazioni
consolidate e non solo coppie.

Due precisazioni che evitano letture sbagliate:

* il numero di triangoli cresce con il numero di passaggi: va normalizzato (per
  passaggio o per minuto) prima di confrontare squadre o partite;
* la direzione dei passaggi conta: una terna collegata solo in due versi non è un
  triangolo, è una catena. Il conteggio qui è sui triangoli completi.

Example:
    >>> from openzone.spatial import triangles
    >>> frame = triangles.triangle_counts(edges)  # doctest: +SKIP
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from openzone._deps import require
from openzone.exceptions import OpenZoneError

__all__ = ["normalise_by_passes", "triangle_counts", "undirected_graph"]

_REQUIRED_EDGES = ("passer_id", "receiver_id", "passes")


def undirected_graph(edges: pd.DataFrame) -> Any:
    """Costruisce il grafo non orientato dei passaggi.

    I triangoli sono una proprietà della struttura, non della direzione: per contarli
    il grafo va reso non orientato, tenendo il peso massimo fra le due direzioni.

    Args:
        edges: Archi prodotti da :func:`openzone.spatial.pass_networks.pass_edges`.

    Returns:
        Un ``networkx.Graph``.

    Raises:
        MissingDependencyError: Se ``networkx`` non è installato.
        OpenZoneError: Se mancano le colonne necessarie.
    """
    networkx = require("networkx")
    missing = [column for column in _REQUIRED_EDGES if column not in edges.columns]
    if missing:
        raise OpenZoneError(f"triangles.undirected_graph: colonne mancanti {', '.join(missing)}")

    graph = networkx.Graph()
    for row in edges.itertuples(index=False):
        weight = int(row.passes)
        if graph.has_edge(row.passer_id, row.receiver_id):
            weight = max(weight, int(graph[row.passer_id][row.receiver_id].get("weight", 0)))
        graph.add_edge(row.passer_id, row.receiver_id, weight=weight)
    return graph


def triangle_counts(graph: Any, *, min_weight: int = 1) -> pd.DataFrame:
    """Conta i triangoli a cui partecipa ogni giocatore.

    Args:
        graph: Grafo non orientato prodotto da :func:`undirected_graph`.
        min_weight: Peso minimo perché un arco conti nel triangolo. Serve a escludere
            le combinazioni occasionali, che gonfiano il conteggio.

    Returns:
        DataFrame con ``player_id`` e ``triangles``, ordinato in modo decrescente.
    """
    networkx = require("networkx")
    filtered = networkx.Graph(
        (u, v, data)
        for u, v, data in graph.edges(data=True)
        if int(data.get("weight", 1)) >= min_weight
    )
    counts = networkx.triangles(filtered)
    frame = pd.DataFrame(
        {"player_id": list(counts), "triangles": list(counts.values())}
    )
    return frame.sort_values("triangles", ascending=False).reset_index(drop=True)


def normalise_by_passes(
    triangle_frame: pd.DataFrame,
    passes: pd.DataFrame,
    *,
    player_column: str = "player_id",
) -> pd.DataFrame:
    """Normalizza il conteggio dei triangoli per i passaggi effettuati.

    Args:
        triangle_frame: Output di :func:`triangle_counts`.
        passes: DataFrame con ``player_id`` e ``passes``, da
            :func:`openzone.spatial.pass_networks.node_strength`.
        player_column: Nome della colonna del giocatore.

    Returns:
        DataFrame con ``triangles_per_100_passes``.

    Raises:
        OpenZoneError: Se mancano le colonne necessarie.
    """
    if player_column not in triangle_frame.columns or player_column not in passes.columns:
        raise OpenZoneError(
            f"triangles.normalise_by_passes: colonna {player_column!r} assente in uno dei due input"
        )
    if "passes" not in passes.columns:
        raise OpenZoneError("triangles.normalise_by_passes: manca la colonna 'passes'")
    merged = triangle_frame.merge(
        passes[[player_column, "passes"]], on=player_column, how="left"
    )
    merged["triangles_per_100_passes"] = (
        100.0 * merged["triangles"] / merged["passes"].replace(0, pd.NA)
    ).astype("Float64")
    return merged.sort_values("triangles_per_100_passes", ascending=False).reset_index(drop=True)
