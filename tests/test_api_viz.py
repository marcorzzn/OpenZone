"""Test dell'API pubblica e delle visualizzazioni."""

from __future__ import annotations

import pandas as pd
import pytest

from openzone import api
from openzone.exceptions import MetricNotFoundError, MissingDependencyError, OpenZoneError
from openzone.viz import passes as passes_viz
from openzone.viz import pitch
from openzone.viz import shots as shots_viz


def test_get_glossary_is_available_from_the_api() -> None:
    """Il glossario è il primo pezzo davvero utilizzabile dell'API."""
    assert api.get_glossary("xT")["generation"] == 3
    with pytest.raises(MetricNotFoundError):
        api.get_glossary("metrica_inesistente")


def test_api_stability_contract_is_stated() -> None:
    """Il contratto di stabilità è dichiarato nel modulo."""
    assert "stabile" in api.API_STABILITY


def test_unimplemented_endpoints_declare_themselves(
    events: pd.DataFrame,
    shots: pd.DataFrame,
) -> None:
    """Le funzioni non pronte falliscono dichiarando la fase della roadmap."""
    with pytest.raises(NotImplementedError):
        api.load_shots(player_id=1, season="2024")
    with pytest.raises(NotImplementedError):
        api.load_events(match_id=1)
    with pytest.raises(NotImplementedError):
        api.compute_xg(shots)
    with pytest.raises(NotImplementedError):
        api.compute_xt(events)


def test_plot_shot_map_requires_a_model_label(shots: pd.DataFrame) -> None:
    """Un xG senza modello dichiarato non finisce in un grafico."""
    with pytest.raises(OpenZoneError, match="model_label"):
        api.plot_shot_map(shots, size_by="xg")


def test_plot_shot_map_needs_the_visualisation_extra(shots: pd.DataFrame) -> None:
    """Con l'etichetta giusta il blocco successivo è la dipendenza mancante."""
    with pytest.raises(MissingDependencyError):
        api.plot_shot_map(shots, size_by="xg", model_label="Understat")


def test_pitch_dimensions_for_known_types() -> None:
    """Le dimensioni del campo corrispondono ai sistemi di coordinate."""
    assert pitch.pitch_dimensions("opta") == {"length": 100.0, "width": 100.0}
    assert pitch.pitch_dimensions("statsbomb") == {"length": 120.0, "width": 80.0}


def test_pitch_dimensions_rejects_unknown_type() -> None:
    """Un tipo di campo non noto è un errore."""
    with pytest.raises(KeyError):
        pitch.pitch_dimensions("campo_inventato")


def test_viz_availability_reports_dependencies() -> None:
    """Lo stato delle dipendenze di visualizzazione è riportato, non assunto."""
    from openzone import viz

    status = viz.available()
    assert set(status) == {"mplsoccer", "matplotlib"}
    assert all(isinstance(value, bool) for value in status.values())


def test_visualisation_functions_require_mplsoccer(events: pd.DataFrame) -> None:
    """Le funzioni di disegno falliscono indicando l'extra da installare.

    ``size_by`` è disattivato esplicitamente: senza di esso la funzione salta la
    verifica sull'etichetta del modello e arriva alla dipendenza mancante, che è ciò
    che questo test verifica.
    """
    with pytest.raises(MissingDependencyError):
        shots_viz.shot_map(events, size_by=None)
    with pytest.raises(MissingDependencyError):
        pitch.draw_pitch()
    with pytest.raises(MissingDependencyError):
        passes_viz.pass_arrows(events)
