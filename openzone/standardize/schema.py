"""Schema canonico degli eventi.

Tutte le fonti convergono su queste colonne. Il contratto è volutamente esplicito e
minimo: se una fonte non ha un'informazione, la colonna esiste comunque ed è vuota.
Un dato mancante non deve diventare zero, e non deve sparire: entrambe le cose
falsano i conteggi a valle senza che nessuno se ne accorga.

Unità e convenzioni:

* coordinate nel sistema Opta normalizzato 100x100, ``x`` verso la porta avversaria,
  ``y`` dall'alto verso il basso;
* l'orientamento è normalizzato: entrambe le squadre attaccano nella stessa direzione
  in tutti i periodi (vedi :func:`openzone.standardize.mapping.normalise_direction`);
* ``qualifiers`` è sempre un dizionario, mai ``None``: un dizionario vuoto significa
  "nessun qualificatore", non "informazione assente".
"""

from __future__ import annotations

from typing import Final

__all__ = ["CANONICAL_EVENT_SCHEMA", "EVENT_FAMILIES", "PITCH_SIZE", "REQUIRED_EVENT_COLUMNS"]

#: Dimensioni del campo normalizzato usato internamente.
PITCH_SIZE: Final[tuple[int, int]] = (100, 100)

#: Colonne dello schema canonico e loro tipo atteso.
CANONICAL_EVENT_SCHEMA: Final[dict[str, str]] = {
    "event_id": "string",
    "match_id": "string",
    "period": "int8",
    "minute": "int16",
    "second": "int16",
    "timestamp": "datetime64[ns]",
    "type_id": "int16",
    "type_name": "string",
    "family": "category",
    "player_id": "string",
    "player_name": "string",
    "team_id": "string",
    "team_name": "string",
    "x": "float32",
    "y": "float32",
    "end_x": "float32",
    "end_y": "float32",
    "outcome": "boolean",
    "qualifiers": "object",
    "source": "category",
}

#: Colonne che non possono essere vuote in una tabella eventi valida.
REQUIRED_EVENT_COLUMNS: Final[tuple[str, ...]] = (
    "event_id",
    "match_id",
    "period",
    "minute",
    "type_name",
    "team_id",
    "source",
)

#: Famiglie di eventi usate dalle metriche. Una famiglia è un insieme di tipi che si
#: comportano allo stesso modo ai fini del calcolo: le metriche lavorano sulle famiglie,
#: non sui nomi dei tipi, così una fonte nuova si integra mappando i suoi tipi.
EVENT_FAMILIES: Final[tuple[str, ...]] = (
    "pass",
    "carry",
    "shot",
    "dribble",
    "duel",
    "defensive",
    "pressure",
    "goalkeeping",
    "foul",
    "discipline",
    "lineup",
    "substitution",
    "match_state",
    "own_goal",
    "error",
    "dead_ball",
    "possession",
    "unknown",
)
