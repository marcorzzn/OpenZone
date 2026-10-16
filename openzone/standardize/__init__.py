"""Standardizzazione: portare fonti diverse su un unico formato.

Tre sottomoduli con responsabilità nette:

* :mod:`~openzone.standardize.schema` definisce lo schema canonico verso cui si
  converge (colonne, tipi, famiglie di eventi);
* :mod:`~openzone.standardize.mapping` fa le conversioni pure: coordinate, orientamenti,
  tipi evento. È l'unico posto dove vivono queste mappature;
* :mod:`~openzone.standardize.kloppy` e :mod:`~openzone.standardize.socceraction`
  delegano a librerie esterne la parte di parsing dei formati e la conversione in SPADL.

Il confine è deliberato: la libreria esterna fa il parsing del formato, OpenZone
decide cosa significa un evento e come si chiama. Quando una libreria cambia API, si
aggiorna un wrapper; quando cambia una definizione, si aggiorna il glossario.

Example:
    >>> from openzone.standardize import CANONICAL_EVENT_SCHEMA
    >>> sorted(CANONICAL_EVENT_SCHEMA)[:3]
    ['end_x', 'end_y', 'event_id']
"""

from __future__ import annotations

from openzone._deps import has
from openzone.standardize.schema import (
    CANONICAL_EVENT_SCHEMA,
    EVENT_FAMILIES,
    PITCH_SIZE,
    REQUIRED_EVENT_COLUMNS,
)

__all__ = [
    "CANONICAL_EVENT_SCHEMA",
    "EVENT_FAMILIES",
    "PITCH_SIZE",
    "REQUIRED_EVENT_COLUMNS",
    "available",
]


def available() -> dict[str, bool]:
    """Riporta la disponibilità dei backend di standardizzazione.

    Returns:
        Mappa ``{"kloppy": bool, "socceraction": bool}``.
    """
    return {"kloppy": has("kloppy"), "socceraction": has("socceraction")}
