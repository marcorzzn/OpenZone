"""Adapter per dataset a livello partita (DataHub e CSV equivalenti).

Fonte minimale: risultati e metadati di partita, senza eventi né coordinate. Serve a
costruire lo scheletro di una stagione (quali partite esistono) su cui innestare gli
eventi di altre fonti.

L'adapter legge file locali in CSV o Parquet; il download è responsabilità
dell'utente, così la provenienza e la licenza del file restano note.

Example:
    >>> from openzone.ingest import datahub
    >>> frame = datahub.load_matches("matches.csv")  # doctest: +SKIP
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from openzone.exceptions import SourceNotAvailableError

__all__ = ["REQUIRED_COLUMNS", "available", "load_matches", "name", "requires"]

#: Chiave della fonte, come in ``glossary/sources.yaml``.
name = "datahub"

#: Moduli opzionali richiesti.
requires: tuple[str, ...] = ()

#: Colonne che il file deve contenere per essere utilizzabile.
REQUIRED_COLUMNS: tuple[str, ...] = ("date", "home_team", "away_team")


def available() -> bool:
    """Indica se l'adapter è utilizzabile.

    Returns:
        Sempre ``True``: legge solo file locali con ``pandas``.
    """
    return True


def load_matches(path: str | Path, **read_kwargs: object) -> pd.DataFrame:
    """Legge un file locale di partite.

    Args:
        path: Percorso del file ``.csv``, ``.parquet`` o ``.json``.
        **read_kwargs: Argomenti aggiuntivi passati alla funzione di lettura di
            ``pandas`` corrispondente all'estensione.

    Returns:
        DataFrame delle partite.

    Raises:
        SourceNotAvailableError: Se il file non esiste, l'estensione non è gestita o
            mancano le colonne minime.
    """
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise SourceNotAvailableError(f"File non trovato: {resolved}")

    suffix = resolved.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(resolved, **read_kwargs)  # type: ignore[arg-type]
    elif suffix == ".parquet":
        frame = pd.read_parquet(resolved, **read_kwargs)
    elif suffix == ".json":
        frame = pd.read_json(resolved, **read_kwargs)  # type: ignore[arg-type]
    else:
        raise SourceNotAvailableError(
            f"Estensione non gestita: {suffix!r}. Usa .csv, .parquet o .json."
        )

    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise SourceNotAvailableError(
            f"Colonne obbligatorie mancanti in {resolved.name}: {', '.join(missing)}"
        )
    frame.attrs["openzone.source"] = name
    frame.attrs["openzone.path"] = str(resolved)
    return frame
