"""Reti di passaggio.

Una rete di passaggio è un grafo in cui i nodi sono i giocatori e gli archi i passaggi
scambiati, pesati per numero di passaggi. Serve a rispondere a domande come: da chi
passa il gioco di una squadra, quali coppie sono connesse, quale giocatore è un ponte
fra reparti.

Due avvertenze che cambiano l'interpretazione del risultato:

* la rete dipende dalla partita e dal risultato: una squadra che insegue passa in modo
  diverso da una che gestisce;
* i pesi grezzi favoriscono chi gioca più minuti: accompagnare sempre il grafo con i
  minuti, altrimenti la rete misura la presenza in campo, non l'importanza.

La costruzione degli archi è pura manipolazione di DataFrame; solo la parte di grafo e
le sue metriche richiedono ``networkx``.

Example:
    >>> from openzone.spatial import pass_networks
    >>> edges = pass_networks.pass_edges(events)  # doctest: +SKIP
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from openzone._deps import require
from openzone.exceptions import OpenZoneError

__all__ = [
    "MINUTES_COLUMN_HINT",
    "node_strength",
    "pass_edges",
    "to_graph",
]

#: Promemoria sul denominatore da usare insieme alla rete.
MINUTES_COLUMN_HINT = (
    "I pesi di una rete di passaggio crescono con i minuti giocati: "
    "normalizza per i minuti prima di confrontare giocatori diversi."
)

#: Colonne necessarie a costruire gli archi.
_REQUIRED_COLUMNS = ("family", "team_id", "player_id", "end_x", "end_y")


def _receiver_column(events: pd.DataFrame) -> str | None:
    """Individua la colonna che identifica il ricevente di un passaggio.

    Args:
        events: Eventi standardizzati.

    Returns:
        Il nome della colonna, oppure ``None`` se la fonte non registra il ricevente.
    """
    for candidate in ("receiver_id", "recipient_id", "pass_recipient_id"):
        if candidate in events.columns:
            return candidate
    return None


def pass_edges(
    events: pd.DataFrame,
    team_id: Any | None = None,
    *,
    completed_only: bool = True,
) -> pd.DataFrame:
    """Costruisce la lista degli archi di passaggio.

    Args:
        events: Eventi standardizzati.
        team_id: Se indicato, limita la rete a una squadra.
        completed_only: Considera solo i passaggi riusciti.

    Returns:
        DataFrame con una riga per coppia ``(passer_id, receiver_id)`` e le colonne
        ``passes``, ``mean_end_x`` e ``mean_end_y``.

    Raises:
        OpenZoneError: Se il ricevente non è identificabile: alcune fonti non
            registrano chi riceve un passaggio, e senza ricevente non esiste un arco.
            In quel caso si può costruire una rete solo sulle zone di arrivo, non sui
            giocatori.
    """
    missing = [column for column in _REQUIRED_COLUMNS if column not in events.columns]
    if missing:
        raise OpenZoneError(
            f"pass_networks.pass_edges: colonne mancanti {', '.join(missing)}"
        )

    receiver = _receiver_column(events)
    if receiver is None:
        raise OpenZoneError(
            "Il ricevente di un passaggio non è identificabile: nessuna delle colonne "
            "receiver_id, recipient_id, pass_recipient_id è presente. "
            "Senza ricevente si possono analizzare le zone di arrivo, non la rete fra "
            "giocatori."
        )

    passes = events.loc[events["family"] == "pass"]
    if team_id is not None:
        passes = passes.loc[passes["team_id"] == team_id]
    if completed_only and "outcome" in passes.columns:
        passes = passes.loc[passes["outcome"].astype("boolean").fillna(False)]
    passes = passes.dropna(subset=["player_id", receiver])

    grouped = passes.groupby(["team_id", "player_id", receiver], observed=True).agg(
        passes=("family", "size"),
        mean_end_x=("end_x", "mean"),
        mean_end_y=("end_y", "mean"),
    )
    return (
        grouped.reset_index()
        .rename(columns={"player_id": "passer_id", receiver: "receiver_id"})
        .sort_values("passes", ascending=False)
        .reset_index(drop=True)
    )


def to_graph(edges: pd.DataFrame) -> Any:
    """Costruisce un grafo orientato e pesato dagli archi di passaggio.

    Args:
        edges: Archi prodotti da :func:`pass_edges`.

    Returns:
        Un ``networkx.DiGraph`` con il numero di passaggi come attributo ``weight``.

    Raises:
        MissingDependencyError: Se ``networkx`` non è installato.
        OpenZoneError: Se mancano le colonne necessarie.
    """
    networkx = require("networkx")
    required = ("passer_id", "receiver_id", "passes")
    missing = [column for column in required if column not in edges.columns]
    if missing:
        raise OpenZoneError(f"pass_networks.to_graph: colonne mancanti {', '.join(missing)}")

    graph = networkx.DiGraph()
    for row in edges.itertuples(index=False):
        graph.add_edge(
            row.passer_id,
            row.receiver_id,
            weight=int(row.passes),
        )
    return graph


def node_strength(graph: Any) -> pd.DataFrame:
    """Calcola la forza dei nodi in entrata e in uscita.

    Args:
        graph: Grafo prodotto da :func:`to_graph`.

    Returns:
        DataFrame con ``player_id``, ``passes_made``, ``passes_received`` e
        ``in_out_ratio`` per ogni giocatore.
    """
    rows: list[dict[str, Any]] = []
    for node in graph.nodes:
        made = sum(data.get("weight", 1) for _, _, data in graph.out_edges(node, data=True))
        received = sum(data.get("weight", 1) for _, _, data in graph.in_edges(node, data=True))
        rows.append(
            {
                "player_id": node,
                "passes_made": int(made),
                "passes_received": int(received),
                "in_out_ratio": (received / made) if made else None,
            }
        )
    return pd.DataFrame(rows).sort_values("passes_made", ascending=False).reset_index(drop=True)
