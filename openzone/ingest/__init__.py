"""Ingestione dati da fonti esterne.

Ogni sottomodulo incapsula una fonte e le sue dipendenze, così un guasto o un
cambiamento di formato resta confinato in un file. Gli adapter restituiscono dati
**grezzi**, con i nomi di colonna della fonte: la normalizzazione avviene in
:mod:`openzone.standardize`.

| Sottomodulo | Fonte | Dipendenze |
|---|---|---|
| :mod:`~openzone.ingest.statsbomb` | StatsBomb Open Data | nessuna obbligatoria (`pandas`) |
| :mod:`~openzone.ingest.soccerdata` | FBref, Understat, FotMob, Sofascore, ... | `soccerdata` |
| :mod:`~openzone.ingest.pannadata` | Opta Parquet locali | `pandas`, `pyarrow` |
| :mod:`~openzone.ingest.understat` | Understat | `soccerdata` |
| :mod:`~openzone.ingest.whoscored` | WhoScored | `soccerdata` |
| :mod:`~openzone.ingest.scraperfc` | Varie (fallback) | `ScraperFC` |
| :mod:`~openzone.ingest.datahub` | DataHub | nessuna obbligatoria |
| :mod:`~openzone.ingest.football_data_org` | football-data.org | `requests` |

Prima di usare una fonte, leggi la sua scheda in ``glossary/sources.yaml``: contiene
licenza, modalità di accesso e limiti d'uso. Alcune fonti vietano lo scraping nei
termini di servizio, e OpenZone non include né ridistribuisce dati di terze parti.

Example:
    >>> from openzone.ingest import adapters, available_adapters
    >>> "statsbomb_open_data" in adapters()
    True
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from types import ModuleType

__all__ = ["adapter", "adapters", "available_adapters"]

#: Mappa chiave-fonte (come in ``glossary/sources.yaml``) -> modulo adapter.
_ADAPTER_MODULES: dict[str, str] = {
    "datahub": "openzone.ingest.datahub",
    "football_data_org": "openzone.ingest.football_data_org",
    "pannadata": "openzone.ingest.pannadata",
    "scraperfc": "openzone.ingest.scraperfc",
    "soccerdata": "openzone.ingest.soccerdata",
    "statsbomb_open_data": "openzone.ingest.statsbomb",
    "understat": "openzone.ingest.understat",
    "whoscored": "openzone.ingest.whoscored",
}


def adapters() -> dict[str, str]:
    """Elenca gli adapter registrati.

    Returns:
        Mappa ``{chiave_fonte: percorso_modulo}``.
    """
    return dict(_ADAPTER_MODULES)


def adapter(name: str) -> ModuleType:
    """Importa l'adapter di una fonte.

    Args:
        name: Chiave della fonte, come in ``glossary/sources.yaml``.

    Returns:
        Il modulo adapter.

    Raises:
        KeyError: Se la fonte non ha un adapter registrato.
    """
    from importlib import import_module

    if name not in _ADAPTER_MODULES:
        known = ", ".join(sorted(_ADAPTER_MODULES))
        raise KeyError(f"Fonte senza adapter: {name!r}. Fonti note: {known}")
    return import_module(_ADAPTER_MODULES[name])


def available_adapters() -> list[str]:
    """Elenca gli adapter utilizzabili nell'ambiente corrente.

    Non esegue richieste di rete: verifica solo che le dipendenze dichiarate siano
    installate.

    Returns:
        Chiavi delle fonti i cui adapter sono pronti all'uso.
    """
    ready: list[str] = []
    for name in sorted(_ADAPTER_MODULES):
        module = adapter(name)
        check = getattr(module, "available", None)
        if callable(check) and check():
            ready.append(name)
    return ready
