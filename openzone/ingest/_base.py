"""Contratto comune agli adapter di ingestione.

Un adapter è un modulo, non una classe: espone funzioni pure che restituiscono
DataFrame e non conserva stato. Questa scelta mantiene gli adapter banali da testare
e da sostituire, e permette di usare gli stessi nomi di funzione fra fonti diverse.

Contratto minimo di ogni adapter:

``name``
    Chiave della fonte, identica a quella usata in
    :mod:`openzone.glossary.sources`.
``requires``
    Moduli opzionali necessari, nell'ordine in cui vanno importati.
``available() -> bool``
    ``True`` se le dipendenze sono installate e, quando serve, le credenziali sono
    presenti nell'ambiente. Non esegue richieste di rete.
``load_matches(...) -> pandas.DataFrame``
    Partite disponibili, nello schema :data:`MATCH_COLUMNS`.
``load_events(match_id, ...) -> pandas.DataFrame``
    Eventi di una partita, nello schema :data:`EVENT_COLUMNS`.

Gli adapter restituiscono lo schema grezzo della fonte, con i nomi di colonna
originali, e non tentano di normalizzare: la normalizzazione è compito di
:mod:`openzone.standardize`. Un adapter che "aggiusta" i dati a metà strada rende
impossibile capire da dove viene un numero.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

__all__ = [
    "EVENT_COLUMNS",
    "MATCH_COLUMNS",
    "IngestAdapter",
]

#: Colonne che una tabella partite deve avere dopo la standardizzazione.
MATCH_COLUMNS: tuple[str, ...] = (
    "match_id",
    "date",
    "competition",
    "season",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
)

#: Colonne che una tabella eventi deve avere dopo la standardizzazione.
EVENT_COLUMNS: tuple[str, ...] = (
    "event_id",
    "match_id",
    "period",
    "minute",
    "second",
    "type_id",
    "type_name",
    "player_id",
    "team_id",
    "x",
    "y",
    "end_x",
    "end_y",
    "outcome",
    "qualifiers",
)


@runtime_checkable
class IngestAdapter(Protocol):
    """Interfaccia strutturale di un adapter di ingestione."""

    #: Chiave della fonte, uguale a quella in ``glossary/sources.yaml``.
    name: str

    #: Moduli opzionali richiesti dall'adapter.
    requires: tuple[str, ...]

    def available(self) -> bool:
        """Indica se l'adapter è utilizzabile nell'ambiente corrente."""
        ...

    def load_matches(self, *args: object, **kwargs: object) -> pd.DataFrame:
        """Restituisce le partite disponibili per la fonte."""
        ...

    def load_events(self, match_id: object, *args: object, **kwargs: object) -> pd.DataFrame:
        """Restituisce gli eventi grezzi di una partita."""
        ...
