"""Caricamento e cache dei file YAML del glossario.

Il glossario è un pacchetto di dati versionati accanto al codice: le definizioni
vivono in YAML, non in Python, così possono essere corrette e riviste da analisti
senza toccare la logica, e possono essere lette anche da OpenPitch o da altri
strumenti senza importare questa libreria.

I file vengono letti una sola volta per processo e tenuti in cache; usa
:func:`clear_cache` nei test che ne modificano il contenuto.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

from openzone._deps import require

__all__ = [
    "DATA_DIR",
    "clear_cache",
    "load_metrics",
    "load_opta_definitions",
    "load_sources",
]

#: Directory che contiene i file YAML del glossario.
DATA_DIR = Path(__file__).resolve().parent

METRICS_FILE = "metrics.yaml"
SOURCES_FILE = "sources.yaml"
OPTA_FILE = "opta_definitions.yaml"


@functools.cache
def _load(file_name: str) -> dict[str, Any]:
    """Legge un file YAML del glossario, con cache per processo.

    Args:
        file_name: Nome del file dentro :data:`DATA_DIR`.

    Returns:
        Il contenuto del file come dizionario.

    Raises:
        FileNotFoundError: Se il file non esiste nel package installato.
        ValueError: Se il file non contiene una mappa YAML al livello superiore.
    """
    path = DATA_DIR / file_name
    if not path.is_file():
        raise FileNotFoundError(f"File di glossario assente: {path}")
    yaml = require("yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} deve contenere una mappa YAML al livello superiore")
    return data


def load_metrics() -> dict[str, Any]:
    """Restituisce l'intero documento ``metrics.yaml``.

    Returns:
        Mappa con ``schema_version``, ``generations`` e la sezione ``metrics``.
    """
    return _load(METRICS_FILE)


def load_sources() -> dict[str, Any]:
    """Restituisce l'intero documento ``sources.yaml``.

    Returns:
        Mappa con ``schema_version`` e la sezione ``sources``.
    """
    return _load(SOURCES_FILE)


def load_opta_definitions() -> dict[str, Any]:
    """Restituisce l'intero documento ``opta_definitions.yaml``.

    Returns:
        Mappa con i tipi evento, i qualificatori e le note di verifica.
    """
    return _load(OPTA_FILE)


def clear_cache() -> None:
    """Svuota la cache dei file YAML letti.

    Example:
        >>> from openzone.glossary import _store
        >>> _store.clear_cache()
    """
    _load.cache_clear()
