"""Terzi di campo, corridoi e half-spaces.

La classificazione a zone è il mattone di base di quasi tutta l'analisi spaziale:
divide il campo in terzi lungo l'asse x e in cinque corridoi lungo l'asse y, di cui due
half-spaces. È pura geometria, quindi questo modulo non ha dipendenze oltre a ``pandas``
e non c'è nulla da approssimare.

Le zone valgono solo se l'orientamento delle coordinate è già normalizzato: applicarle
a coordinate grezze mescola primo e secondo tempo.

Convenzione sull'asse y: nello schema canonico y cresce dall'alto verso il basso, quindi
"sinistra" e "destra" si riferiscono al punto di vista di chi guarda il campo dall'alto
con l'attacco verso destra. Per evitare ambiguità i nomi delle colonne sono neutri
(``channel`` con valori ``left``/``right``) e la loro interpretazione calcistica va
dichiarata insieme al grafico.

Example:
    >>> from openzone.spatial.half_spaces import classify_channels, classify_thirds
    >>> classify_thirds(20.0)
    'defensive_third'
    >>> classify_channels(45.0)
    'centre'
"""

from __future__ import annotations

import pandas as pd

from openzone.exceptions import OpenZoneError

__all__ = [
    "CHANNELS",
    "CHANNEL_BOUNDS",
    "THIRDS",
    "classify",
    "classify_channels",
    "classify_thirds",
    "is_half_space",
    "zone_counts",
]

#: Nomi dei terzi di campo, dall'area propria a quella avversaria.
THIRDS: tuple[str, ...] = ("defensive_third", "middle_third", "final_third")

#: Nomi dei cinque corridoi, da y=0 a y=100 nello schema canonico.
CHANNELS: tuple[str, ...] = (
    "left_wing",
    "left_half_space",
    "centre",
    "right_half_space",
    "right_wing",
)

#: Limiti superiori dei corridoi, in percentuale dell'asse y.
CHANNEL_BOUNDS: tuple[float, ...] = (20.0, 40.0, 60.0, 80.0)

#: Corridoi considerati half-spaces.
_HALF_SPACES = frozenset({"left_half_space", "right_half_space"})


def classify_thirds(x: float, pitch_size: float = 100.0) -> str:
    """Classifica una coordinata x in un terzo di campo.

    Args:
        x: Coordinata x nello schema canonico.
        pitch_size: Estensione dell'asse x.

    Returns:
        Nome del terzo.

    Example:
        >>> [classify_thirds(value) for value in (10.0, 50.0, 90.0)]
        ['defensive_third', 'middle_third', 'final_third']
    """
    third = min(2, max(0, int(x / (pitch_size / 3))))
    return THIRDS[third]


def classify_channels(y: float) -> str:
    """Classifica una coordinata y in un corridoio.

    Args:
        y: Coordinata y nello schema canonico.

    Returns:
        Nome del corridoio.

    Example:
        >>> classify_channels(10.0)
        'left_wing'
        >>> classify_channels(50.0)
        'centre'
    """
    if y < CHANNEL_BOUNDS[0]:
        return CHANNELS[0]
    if y < CHANNEL_BOUNDS[1]:
        return CHANNELS[1]
    if y < CHANNEL_BOUNDS[2]:
        return CHANNELS[2]
    if y < CHANNEL_BOUNDS[3]:
        return CHANNELS[3]
    return CHANNELS[4]


def is_half_space(y: float) -> bool:
    """Indica se una coordinata y cade in un half-space.

    Args:
        y: Coordinata y nello schema canonico.

    Returns:
        ``True`` se la coordinata è in uno dei due half-spaces.
    """
    return classify_channels(y) in _HALF_SPACES


def classify(events: pd.DataFrame, *, x_column: str = "x", y_column: str = "y") -> pd.DataFrame:
    """Aggiunge le colonne di zona a una tabella di eventi.

    Args:
        events: Eventi standardizzati.
        x_column: Nome della colonna con la coordinata x.
        y_column: Nome della colonna con la coordinata y.

    Returns:
        Una copia di ``events`` con le colonne ``third``, ``channel``, ``half_space`` e
        ``zone``. Le righe senza coordinate restano con valori mancanti: non vengono
        assegnate a una zona a caso.

    Raises:
        OpenZoneError: Se mancano le colonne delle coordinate.
    """
    missing = [column for column in (x_column, y_column) if column not in events.columns]
    if missing:
        raise OpenZoneError(
            f"half_spaces.classify: colonne mancanti {', '.join(missing)}"
        )
    result = events.copy()
    has_coordinates = result[[x_column, y_column]].notna().all(axis=1)
    x = result[x_column].astype("float64")
    y = result[y_column].astype("float64")

    # Le liste sono costruite prima di toccare il DataFrame: passare per una colonna
    # intermedia converte i ``None`` in ``NaN``, e un evento senza coordinate finirebbe
    # in una zona chiamata "nan_nan".
    thirds = [
        classify_thirds(value) if present else None
        for value, present in zip(x, has_coordinates, strict=True)
    ]
    channels = [
        classify_channels(value) if present else None
        for value, present in zip(y, has_coordinates, strict=True)
    ]
    half_spaces = [
        is_half_space(value) if present else None
        for value, present in zip(y, has_coordinates, strict=True)
    ]
    zones = [
        f"{third}_{channel}" if third is not None and channel is not None else None
        for third, channel in zip(thirds, channels, strict=True)
    ]

    result["third"] = pd.Series(thirds, index=result.index, dtype="object")
    result["channel"] = pd.Series(channels, index=result.index, dtype="object")
    result["half_space"] = pd.Series(half_spaces, index=result.index, dtype="object")
    result["zone"] = pd.Series(zones, index=result.index, dtype="object")
    return result


def zone_counts(
    events: pd.DataFrame,
    by: str = "team_id",
    *,
    zone_column: str = "zone",
) -> pd.DataFrame:
    """Conta gli eventi per zona e per gruppo.

    Args:
        events: Eventi con le colonne di zona, prodotti da :func:`classify`.
        by: Colonna di raggruppamento.
        zone_column: Nome della colonna di zona.

    Returns:
        DataFrame con una riga per ``(by, zone)`` e la colonna ``events``.

    Raises:
        OpenZoneError: Se la colonna di zona non è presente: va chiamato prima
            :func:`classify`.
    """
    if zone_column not in events.columns:
        raise OpenZoneError(
            f"Colonna di zona assente: {zone_column!r}. Chiama half_spaces.classify prima."
        )
    if by not in events.columns:
        raise OpenZoneError(f"Colonna di raggruppamento assente: {by!r}")
    counts = (
        events.dropna(subset=[zone_column])
        .groupby([by, zone_column], observed=True)
        .size()
        .rename("events")
        .reset_index()
    )
    return counts.sort_values("events", ascending=False).reset_index(drop=True)
