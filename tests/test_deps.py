"""Test del caricamento pigro delle dipendenze opzionali."""

from __future__ import annotations

import pytest

from openzone import _deps
from openzone.exceptions import MissingDependencyError, OpenZoneError


def test_has_returns_false_for_absent_module() -> None:
    """Un modulo inesistente non è disponibile."""
    assert _deps.has("modulo_inesistente_openzone_xyz") is False


def test_require_raises_with_extra_hint() -> None:
    """Il modulo mancante produce un messaggio che dice quale extra installare."""
    with pytest.raises(MissingDependencyError) as excinfo:
        _deps.require("duckdb")
    message = str(excinfo.value)
    assert "duckdb" in message
    assert "openzone[warehouse]" in message


def test_missing_dependency_error_is_import_error_and_domain_error() -> None:
    """L'errore è sia di dominio sia di import: si può catturare in entrambi i modi."""
    error = MissingDependencyError("duckdb", "warehouse")
    assert isinstance(error, OpenZoneError)
    assert isinstance(error, ImportError)
    assert error.package == "duckdb"
    assert error.extra == "warehouse"


def test_require_any_raises_when_nothing_available() -> None:
    """``require_any`` fallisce elencando i moduli provati."""
    with pytest.raises(MissingDependencyError) as excinfo:
        _deps.require_any(["modulo_inesistente_a", "modulo_inesistente_b"])
    assert "modulo_inesistente_a" in str(excinfo.value)


def test_missing_lists_only_absent_modules() -> None:
    """``missing`` restituisce i soli moduli non installati."""
    absent = _deps.missing(["pandas", "modulo_inesistente_openzone_xyz"])
    assert absent == ["modulo_inesistente_openzone_xyz"]


def test_as_table_covers_known_modules() -> None:
    """La tabella riepiloga i moduli noti con il loro extra."""
    table = _deps.as_table()
    assert table["duckdb"]["extra"] == "warehouse"
    assert table["sklearn"]["extra"] == "models"
    assert table["yaml"]["extra"] == "core"
    assert isinstance(table["yaml"]["installed"], bool)
