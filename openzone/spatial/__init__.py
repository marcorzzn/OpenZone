"""Analisi spaziale, ispirata a Soccermatics.

Qui si studia *dove* succedono le cose: reti di passaggio, triangoli, corridoi e
half-spaces, zone di pressing, controllo del campo.

La scelta di fondo è reimplementare i concetti in Python invece di chiamare le
funzioni R di Soccermatics via ``rpy2``: una dipendenza da R renderebbe la libreria
non installabile con ``pip`` e non testabile in CI. Il debito verso Soccermatics è
culturale — i concetti e i riferimenti — e va dichiarato nelle schede del glossario.

Principio comune a tutti i sottomoduli: le metriche spaziali richiedono che
l'orientamento delle coordinate sia già normalizzato fra i periodi. Applicarle a
coordinate grezze somma il primo e il secondo tempo come se fossero la stessa cosa.

Example:
    >>> from openzone.spatial import ZONES_COLUMNS
    >>> "zone" in ZONES_COLUMNS
    True
"""

from __future__ import annotations

from typing import Final

from openzone._deps import has

__all__ = ["ZONES_COLUMNS", "available", "requires_networkx"]

#: Colonne aggiunte dalle funzioni di classificazione a zone.
ZONES_COLUMNS: Final[tuple[str, ...]] = ("zone", "third", "channel", "half_space")


def requires_networkx() -> bool:
    """Indica se ``networkx`` è installato.

    Le funzioni che costruiscono grafi (reti di passaggio, triangoli) lo richiedono.

    Returns:
        ``True`` se la libreria è importabile.
    """
    return has("networkx")


def available() -> dict[str, bool]:
    """Riporta la disponibilità delle dipendenze dell'analisi spaziale.

    Returns:
        Mappa ``{"networkx": bool}``.
    """
    return {"networkx": requires_networkx()}
