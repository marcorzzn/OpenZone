"""Adapter per i file Parquet di ``pannadata`` (eventi Opta).

Questa fonte è la più ricca per la Serie A (eventi Opta completi di qualificatori e
coordinate), ma è anche la più delicata dal punto di vista legale: i dati Opta sono
proprietari e il repository ``pannadata`` non ne dichiara la licenza.

Conseguenze di progetto, non negoziabili:

* l'adapter lavora **solo su file locali** forniti dall'utente: non scarica nulla;
* non versiona, non copia e non ridistribuisce dati;
* ogni DataFrame restituito porta con sé la provenienza del file letto, così un
  numero calcolato da dati Opta resta riconoscibile a valle.

Example:
    >>> from openzone.ingest import pannadata
    >>> frame = pannadata.load_events("D:/opta/serie_a_2024.parquet")  # doctest: +SKIP
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from openzone._deps import require
from openzone.exceptions import MissingDependencyError, SourceNotAvailableError

__all__ = [
    "available",
    "columns_of",
    "load_events",
    "load_matches",
    "name",
    "requires",
]

#: Chiave della fonte, come in ``glossary/sources.yaml``.
name = "pannadata"

#: Moduli opzionali richiesti per leggere i Parquet.
requires: tuple[str, ...] = ("pyarrow",)

#: Nomi possibili della colonna partita nei file Opta, in ordine di preferenza.
MATCH_ID_CANDIDATES: tuple[str, ...] = ("match_id", "matchId", "game_id", "id")


def available() -> bool:
    """Indica se l'adapter può leggere i Parquet in questo ambiente.

    Returns:
        ``True`` se è installato un motore Parquet.
    """
    from openzone._deps import has

    return has("pyarrow") or has("fastparquet")


def _resolve(path: str | Path) -> Path:
    """Verifica che il file esista e restituisce il percorso assoluto.

    Args:
        path: Percorso del file Parquet indicato dall'utente.

    Returns:
        Il percorso assoluto risolto.

    Raises:
        SourceNotAvailableError: Se il file non esiste o non è un file regolare.
    """
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise SourceNotAvailableError(
            f"File pannadata non trovato: {resolved}. "
            "L'adapter legge solo file locali: nessun download automatico."
        )
    return resolved


def load_events(
    path: str | Path,
    columns: list[str] | None = None,
    **read_kwargs: Any,
) -> pd.DataFrame:
    """Legge un file Parquet di eventi Opta.

    Args:
        path: Percorso del file Parquet.
        columns: Sottoinsieme di colonne da leggere. Consigliato su file grandi,
            perché un file Opta completo può superare il gigabyte.
        **read_kwargs: Argomenti aggiuntivi passati a ``pandas.read_parquet``.

    Returns:
        DataFrame degli eventi, con le colonne originali del file.

    Raises:
        SourceNotAvailableError: Se il file non esiste.
        MissingDependencyError: Se manca un motore Parquet.
    """
    resolved = _resolve(path)
    if not available():
        raise MissingDependencyError("pyarrow", "ingest")
    frame = pd.read_parquet(resolved, columns=columns, **read_kwargs)
    frame.attrs["openzone.source"] = name
    frame.attrs["openzone.path"] = str(resolved)
    return frame


def load_matches(path: str | Path, **read_kwargs: Any) -> pd.DataFrame:
    """Legge un file Parquet a livello partita.

    Args:
        path: Percorso del file Parquet.
        **read_kwargs: Argomenti aggiuntivi passati a ``pandas.read_parquet``.

    Returns:
        DataFrame delle partite.
    """
    return load_events(path, **read_kwargs)


def columns_of(path: str | Path) -> list[str]:
    """Elenca le colonne di un file Parquet senza leggerne i dati.

    Serve a decidere quali colonne caricare su file grandi, che è la differenza fra
    un secondo e qualche minuto di attesa.

    Args:
        path: Percorso del file Parquet.

    Returns:
        Nomi delle colonne nell'ordine del file.
    """
    resolved = _resolve(path)
    pyarrow = require("pyarrow")
    schema = pyarrow.parquet.read_schema(resolved)
    return list(schema.names)
