"""Standardizzazione dei formati tramite ``kloppy``.

``kloppy`` legge i formati dei provider (Opta F7/F24, StatsBomb, Wyscout, SkillCorner,
Second Spectrum, ...) e li espone con un modello dati unico: un oggetto ``Dataset`` con
metadati, formazioni, periodi ed eventi tipizzati.

OpenZone usa ``kloppy`` per il parsing e applica sopra il proprio schema canonico
(:data:`openzone.standardize.CANONICAL_EVENT_SCHEMA`), perché il modello di ``kloppy``
resta specifico della libreria e non va fatto filtrare fino all'API pubblica: un
cambio di versione di ``kloppy`` non deve rompere il codice di un analista.

Example:
    >>> from openzone.standardize import kloppy
    >>> kloppy.available()
    False
    >>> frame = kloppy.to_frame("opta", "f24.xml")  # doctest: +SKIP
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from openzone._deps import has, require

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

__all__ = ["PROVIDERS", "available", "dataset", "to_frame"]

#: Nome della funzione ``kloppy`` che legge ciascun provider.
PROVIDERS: dict[str, str] = {
    "opta": "load_opta",
    "statsbomb": "load_statsbomb",
    "wyscout": "load_wyscout",
    "skillcorner": "load_skillcorner",
    "secondspectrum": "load_secondspectrum",
    "metrica": "load_metrica",
    "sportec": "load_sportec",
    "hawkeye": "load_hawkeye",
}


def available() -> bool:
    """Indica se ``kloppy`` è installato.

    Returns:
        ``True`` se la libreria è importabile.
    """
    return has("kloppy")


def dataset(provider: str, source: str | Path, **kwargs: Any) -> Any:
    """Carica un dataset con ``kloppy``.

    Args:
        provider: Chiave del provider, fra quelle in :data:`PROVIDERS`.
        source: Percorso del file o della directory che contiene i dati.
        **kwargs: Argomenti aggiuntivi passati alla funzione di caricamento, per
            esempio ``coordinates`` o ``additional_metadata``.

    Returns:
        L'oggetto ``Dataset`` di ``kloppy``. Non è un DataFrame: contiene metadati,
        formazioni, periodi ed eventi tipizzati.

    Raises:
        MissingDependencyError: Se ``kloppy`` non è installato.
        KeyError: Se il provider non è supportato.
    """
    if provider not in PROVIDERS:
        known = ", ".join(sorted(PROVIDERS))
        raise KeyError(f"Provider non supportato: {provider!r}. Provider noti: {known}")
    module = require("kloppy")
    loader = getattr(module, PROVIDERS[provider])
    return loader(str(source), **kwargs)


def to_frame(provider: str, source: str | Path, **kwargs: Any) -> pd.DataFrame:
    """Carica un dataset e lo converte nello schema canonico di OpenZone.

    La conversione applica: rinominazione delle colonne, mappatura dei tipi in
    famiglie canoniche, conversione delle coordinate al sistema Opta 100x100 e
    normalizzazione dell'orientamento fra i periodi.

    Args:
        provider: Chiave del provider.
        source: Percorso del file o della directory dei dati.
        **kwargs: Argomenti aggiuntivi passati al caricamento.

    Returns:
        DataFrame conforme a :data:`openzone.standardize.CANONICAL_EVENT_SCHEMA`.

    Raises:
        NotImplementedError: La conversione allo schema canonico è prevista nella
            Fase 1 della roadmap e non è ancora implementata.
    """
    dataset(provider, source, **kwargs)
    raise NotImplementedError(
        "openzone.standardize.kloppy.to_frame: conversione allo schema canonico "
        "prevista in Fase 1 (vedi OPENZONE_BLUEPRINT.md §8)."
    )


def events_frame(dataset_object: Any) -> pd.DataFrame:
    """Estrae gli eventi da un ``Dataset`` di ``kloppy`` come DataFrame.

    Args:
        dataset_object: Oggetto ``Dataset`` restituito da :func:`dataset`.

    Returns:
        DataFrame degli eventi, con le colonne del modello ``kloppy``.

    Raises:
        TypeError: Se l'oggetto non espone un attributo ``events``.
    """
    events = getattr(dataset_object, "events", None)
    if events is None:
        raise TypeError("L'oggetto passato non è un Dataset di kloppy con eventi")
    return events.to_df()
