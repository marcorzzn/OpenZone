"""Adapter di fallback per ``ScraperFC``.

``ScraperFC`` copre fonti che ``soccerdata`` non copre o copre male (per esempio
fotmob, sofascore e alcuni feed di tiro). È il secondo tentativo, non il primo: si
usa quando :mod:`openzone.ingest.soccerdata` non espone il dato che serve.

Restano valide le avvertenze sui termini di servizio: anche ``ScraperFC`` effettua
scraping, e la libreria non trasferisce alcun permesso. Verifica la scheda della
fonte in ``glossary/sources.yaml`` prima dell'uso.

Example:
    >>> from openzone.ingest import scraperfc
    >>> scraperfc.available()
    False
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from openzone._deps import has, require

__all__ = ["available", "client", "load_shots", "name", "requires"]

#: Chiave della fonte, come in ``glossary/sources.yaml``.
name = "scraperfc"

#: Moduli opzionali richiesti.
requires: tuple[str, ...] = ("scraperfc",)

#: Classi di ``ScraperFC`` utilizzabili come fallback, per chiave breve.
SCRAPERS: dict[str, str] = {
    "fbref": "FBref",
    "fotmob": "FotMob",
    "sofascore": "Sofascore",
    "understat": "Understat",
    "whoscored": "WhoScored",
}


def available() -> bool:
    """Indica se ``ScraperFC`` è installato.

    Returns:
        ``True`` se la libreria è importabile.
    """
    return has("scraperfc")


def client(source: str = "sofascore") -> Any:
    """Istanzia uno scraper di ``ScraperFC``.

    Args:
        source: Chiave breve della fonte, fra quelle in :data:`SCRAPERS`.

    Returns:
        Un'istanza dello scraper.

    Raises:
        MissingDependencyError: Se ``ScraperFC`` non è installato.
        KeyError: Se la fonte non è gestita.
    """
    if source not in SCRAPERS:
        known = ", ".join(sorted(SCRAPERS))
        raise KeyError(f"Fonte non gestita: {source!r}. Fonti note: {known}")
    module = require("scraperfc")
    return getattr(module, SCRAPERS[source])()


def load_shots(source: str = "sofascore", *args: Any, **kwargs: Any) -> pd.DataFrame:
    """Legge gli eventi di tiro da una fonte coperta da ``ScraperFC``.

    Args:
        source: Chiave breve della fonte.
        *args: Argomenti posizionali dello scraper.
        **kwargs: Argomenti con nome dello scraper.

    Returns:
        DataFrame dei tiri, con le colonne originali della fonte.
    """
    scraper = client(source)
    return scraper.scrape_match_shots(*args, **kwargs)
