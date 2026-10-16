"""Mappature fra sistemi di coordinate, tipi evento e orientamenti.

Questo modulo è puro Python, senza ``pandas``: le conversioni sono aritmetica su
coordinate e mappe di nomi, e tenerle indipendenti dai DataFrame le rende verificabili
con test banali e riutilizzabili in qualunque punto della pipeline.

Le due cose che questo modulo fa, e che sono la causa più frequente di numeri
sbagliati nelle analisi calcistiche:

1. **convertire le coordinate** fra sistemi diversi (StatsBomb 120x80, Opta 100x100,
   Wyscout 100x100) senza perdere l'orientamento dell'asse y, che cambia da fonte a
   fonte;
2. **normalizzare l'orientamento**, ribaltando le coordinate nel secondo tempo e nei
   tempi supplementari, così che entrambe le squadre attacchino sempre verso lo stesso
   lato del campo.

Example:
    >>> from openzone.standardize.mapping import convert_coordinates
    >>> convert_coordinates(60.0, 40.0, source="statsbomb", target="opta")
    (50.0, 50.0)
    >>> from openzone.standardize.mapping import normalise_direction
    >>> normalise_direction(20.0, 30.0, period=2, flip_odd_periods=True)
    (80.0, 70.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__ = [
    "COORDINATE_SYSTEMS",
    "CoordinateSystem",
    "canonical_family",
    "convert_coordinates",
    "flip_x",
    "flip_y",
    "normalise_direction",
]

#: Statistiche di un sistema di coordinate.
#
#: Attributes:
#:     name: Chiave del sistema.
#:     length: Estensione dell'asse x (lunghezza del campo).
#:     width: Estensione dell'asse y (larghezza del campo).
#:     y_axis_downwards: ``True`` se l'asse y cresce dall'alto verso il basso.
#:     attacks_left_to_right: ``True`` se x cresce verso la porta avversaria.


@dataclass(frozen=True)
class CoordinateSystem:
    """Descrizione di un sistema di coordinate di una fonte."""

    name: str
    length: float
    width: float
    y_axis_downwards: bool
    attacks_left_to_right: bool


#: Sistemi di coordinate noti.
COORDINATE_SYSTEMS: Final[dict[str, CoordinateSystem]] = {
    "opta": CoordinateSystem("opta", 100.0, 100.0, True, True),
    "statsbomb": CoordinateSystem("statsbomb", 120.0, 80.0, True, True),
    "wyscout": CoordinateSystem("wyscout", 100.0, 100.0, True, True),
    "opta_metrica": CoordinateSystem("opta_metrica", 100.0, 100.0, False, True),
}

#: Famiglia canonica per tipo evento StatsBomb.
STATSBOMB_FAMILIES: Final[dict[str, str]] = {
    "Ball Receipt*": "possession",
    "Ball Recovery": "defensive",
    "Bad Behaviour": "discipline",
    "Block": "defensive",
    "Camera On": "match_state",
    "Camera off": "match_state",
    "Carry": "carry",
    "Clearance": "defensive",
    "Dispossessed": "possession",
    "Dribble": "dribble",
    "Dribbled Past": "defensive",
    "Duel": "duel",
    "Error": "error",
    "50/50": "duel",
    "Foul Committed": "foul",
    "Foul Won": "foul",
    "Goal Keeper": "goalkeeping",
    "Half End": "match_state",
    "Half Start": "match_state",
    "Injury Stoppage": "match_state",
    "Interception": "defensive",
    "Miscontrol": "error",
    "Own Goal Against": "own_goal",
    "Own Goal For": "own_goal",
    "Pass": "pass",
    "Player Off": "lineup",
    "Player On": "lineup",
    "Pressure": "pressure",
    "Referee Ball-Drop": "dead_ball",
    "Shield": "possession",
    "Shot": "shot",
    "Starting XI": "lineup",
    "Substitution": "substitution",
    "Tactical Shift": "lineup",
}

#: Famiglia canonica per ``type_id`` Opta. Rispecchia
#: ``openzone/glossary/opta_definitions.yaml``, che resta la fonte delle definizioni:
#: qui c'è solo la classificazione necessaria al calcolo.
OPTA_FAMILIES: Final[dict[int, str]] = {
    1: "pass",
    2: "pass",
    3: "dribble",
    4: "foul",
    5: "dead_ball",
    6: "dead_ball",
    7: "defensive",
    8: "defensive",
    9: "possession",
    10: "goalkeeping",
    11: "goalkeeping",
    12: "defensive",
    13: "shot",
    14: "shot",
    15: "shot",
    16: "shot",
    17: "discipline",
    18: "lineup",
    19: "lineup",
    20: "lineup",
    21: "lineup",
    22: "lineup",
    23: "lineup",
    24: "match_state",
    25: "match_state",
    27: "match_state",
    28: "match_state",
    30: "match_state",
    32: "match_state",
    34: "lineup",
    35: "lineup",
    36: "lineup",
    37: "match_state",
    38: "match_state",
    39: "match_state",
    40: "lineup",
    41: "goalkeeping",
    42: "dribble",
    43: "match_state",
    44: "duel",
    45: "duel",
    46: "defensive",
    47: "match_state",
    48: "match_state",
}


def canonical_family(source: str, identifier: str | int) -> str:
    """Determina la famiglia canonica di un tipo evento.

    Args:
        source: Chiave della fonte (``"statsbomb"``, ``"opta"``, ...).
        identifier: Nome del tipo (StatsBomb) oppure ``type_id`` numerico (Opta).

    Returns:
        La famiglia canonica, o ``"unknown"`` se il tipo non è mappato. Un tipo non
        mappato non va mai indovinato: viene contato come sconosciuto, così il buco
        resta visibile.

    Example:
        >>> canonical_family("statsbomb", "Carry")
        'carry'
        >>> canonical_family("opta", 16)
        'shot'
        >>> canonical_family("opta", 9999)
        'unknown'
    """
    key = source.strip().lower()
    if key == "statsbomb":
        return STATSBOMB_FAMILIES.get(str(identifier), "unknown")
    if key in {"opta", "pannadata"}:
        try:
            return OPTA_FAMILIES.get(int(identifier), "unknown")
        except (TypeError, ValueError):
            return "unknown"
    return "unknown"


def convert_coordinates(
    x: float,
    y: float,
    source: str,
    target: str = "opta",
) -> tuple[float, float]:
    """Converte una coordinata fra due sistemi noti.

    Args:
        x: Coordinata x nel sistema di partenza.
        y: Coordinata y nel sistema di partenza.
        source: Chiave del sistema di partenza.
        target: Chiave del sistema di arrivo.

    Returns:
        La coppia ``(x, y)`` nel sistema di arrivo.

    Raises:
        KeyError: Se uno dei due sistemi non è in :data:`COORDINATE_SYSTEMS`.

    Example:
        >>> convert_coordinates(120.0, 80.0, "statsbomb", "opta")
        (100.0, 100.0)
    """
    origin = COORDINATE_SYSTEMS[source]
    destination = COORDINATE_SYSTEMS[target]
    scaled_x = x / origin.length * destination.length
    scaled_y = y / origin.width * destination.width
    if origin.y_axis_downwards != destination.y_axis_downwards:
        scaled_y = destination.width - scaled_y
    return (scaled_x, scaled_y)


def flip_x(x: float, length: float = 100.0) -> float:
    """Ribalta una coordinata x rispetto all'asse centrale del campo.

    Args:
        x: Coordinata x.
        length: Estensione dell'asse x.

    Returns:
        La coordinata ribaltata.
    """
    return length - x


def flip_y(y: float, width: float = 100.0) -> float:
    """Ribalta una coordinata y rispetto all'asse centrale del campo.

    Args:
        y: Coordinata y.
        width: Estensione dell'asse y.

    Returns:
        La coordinata ribaltata.
    """
    return width - y


def normalise_direction(
    x: float,
    y: float,
    period: int,
    *,
    flip_odd_periods: bool = True,
    length: float = 100.0,
    width: float = 100.0,
) -> tuple[float, float]:
    """Ribalta le coordinate nei periodi in cui la squadra cambia lato.

    Le fonti registrano le coordinate rispetto al campo reale: nel secondo tempo le
    squadre si scambiano i lati, quindi un tiro verso la porta avversaria nel primo
    tempo e uno nel secondo hanno coordinate speculari. Senza questa normalizzazione
    ogni analisi spaziale che aggrega i due tempi somma due cose diverse.

    Args:
        x: Coordinata x nel periodo indicato.
        y: Coordinata y nel periodo indicato.
        period: Numero del periodo (1 e 2 per i tempi regolamentari, 3 e 4 per i
            supplementari, 5 per i rigori).
        flip_odd_periods: Se ``True``, ribalta i periodi pari. È la convenzione
            corretta quando si vuole che la squadra di casa attacchi sempre verso x
            crescente nel primo tempo.
        length: Estensione dell'asse x.
        width: Estensione dell'asse y.

    Returns:
        La coppia ``(x, y)`` normalizzata.

    Raises:
        ValueError: Se ``period`` è minore di 1.

    Example:
        >>> normalise_direction(20.0, 30.0, period=1)
        (20.0, 30.0)
        >>> normalise_direction(20.0, 30.0, period=2)
        (80.0, 70.0)
    """
    if period < 1:
        raise ValueError(f"period deve essere >= 1, ricevuto: {period}")
    if not flip_odd_periods or period % 2 == 1:
        return (x, y)
    return (flip_x(x, length), flip_y(y, width))
