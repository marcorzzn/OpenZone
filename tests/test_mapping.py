"""Test delle mappature: coordinate, orientamenti, famiglie di eventi."""

from __future__ import annotations

import pytest

from openzone.standardize.mapping import (
    COORDINATE_SYSTEMS,
    canonical_family,
    convert_coordinates,
    flip_x,
    flip_y,
    normalise_direction,
)


def test_convert_coordinates_statsbomb_to_opta() -> None:
    """Le coordinate StatsBomb 120x80 diventano 100x100."""
    assert convert_coordinates(120.0, 80.0, "statsbomb", "opta") == (100.0, 100.0)
    assert convert_coordinates(60.0, 40.0, "statsbomb", "opta") == (50.0, 50.0)


def test_convert_coordinates_identity() -> None:
    """Convertire verso lo stesso sistema non cambia nulla."""
    assert convert_coordinates(37.5, 12.5, "opta", "opta") == (37.5, 12.5)


def test_convert_coordinates_flips_y_when_axis_differs() -> None:
    """Un sistema con asse y invertito produce la coordinata ribaltata."""
    flipped = convert_coordinates(50.0, 20.0, "opta", "opta_metrica")
    assert flipped == (50.0, 80.0)


def test_convert_coordinates_unknown_system() -> None:
    """Un sistema non registrato fallisce invece di indovinare."""
    with pytest.raises(KeyError):
        convert_coordinates(1.0, 1.0, "sistema_inesistente", "opta")


def test_coordinate_systems_are_declared_consistently() -> None:
    """Ogni sistema dichiara dimensioni positive e coerenza con la propria chiave."""
    for key, system in COORDINATE_SYSTEMS.items():
        assert system.name == key
        assert system.length > 0
        assert system.width > 0


def test_flip_helpers() -> None:
    """I ribaltamenti rispettano l'estensione indicata."""
    assert flip_x(20.0) == 80.0
    assert flip_y(30.0, width=100.0) == 70.0
    assert flip_x(20.0, length=120.0) == 100.0


def test_normalise_direction_flips_only_even_periods() -> None:
    """Il secondo tempo viene ribaltato, il primo no."""
    assert normalise_direction(20.0, 30.0, period=1) == (20.0, 30.0)
    assert normalise_direction(20.0, 30.0, period=2) == (80.0, 70.0)
    assert normalise_direction(20.0, 30.0, period=3) == (20.0, 30.0)


def test_normalise_direction_can_be_disabled() -> None:
    """Il ribaltamento è disattivabile quando le fonti sono già normalizzate."""
    assert normalise_direction(20.0, 30.0, period=2, flip_odd_periods=False) == (20.0, 30.0)


def test_normalise_direction_rejects_invalid_period() -> None:
    """Un periodo non valido è un errore, non un valore di default silenzioso."""
    with pytest.raises(ValueError):
        normalise_direction(1.0, 1.0, period=0)


def test_canonical_family_for_statsbomb_names() -> None:
    """I nomi StatsBomb sono mappati alle famiglie canoniche."""
    assert canonical_family("statsbomb", "Pass") == "pass"
    assert canonical_family("statsbomb", "Carry") == "carry"
    assert canonical_family("statsbomb", "Shot") == "shot"


def test_canonical_family_for_opta_ids() -> None:
    """I type_id Opta sono mappati alle famiglie canoniche."""
    assert canonical_family("opta", 16) == "shot"
    assert canonical_family("pannadata", 1) == "pass"
    assert canonical_family("opta", "8") == "defensive"


def test_canonical_family_unknown_is_never_guessed() -> None:
    """Un tipo non mappato resta sconosciuto, in tutte le sue forme."""
    assert canonical_family("opta", 9999) == "unknown"
    assert canonical_family("statsbomb", "Evento Nuovo") == "unknown"
    assert canonical_family("fonte_ignota", "Pass") == "unknown"
    assert canonical_family("opta", None) == "unknown"
