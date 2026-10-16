"""Test delle metriche di 1ª generazione."""

from __future__ import annotations

import pandas as pd
import pytest

from openzone.exceptions import OpenZoneError
from openzone.metrics import basic


def test_shots_and_goals_are_counted_from_the_fixture(events: pd.DataFrame) -> None:
    """I tiri e i gol corrispondono agli eventi della fixture."""
    assert len(basic.shots(events)) == 2
    assert len(basic.goals(events)) == 1
    assert list(basic.goals(events)["event_id"]) == ["e5"]


def test_shot_counts_by_player(events: pd.DataFrame) -> None:
    """Il conteggio per giocatore separa tiri, gol e conversione."""
    counts = basic.shot_counts(events)
    assert int(counts.loc["p4", "shots"]) == 1
    assert int(counts.loc["p4", "goals"]) == 1
    assert int(counts.loc["p3", "shots"]) == 1
    assert int(counts.loc["p3", "goals"]) == 0
    assert float(counts.loc["p4", "conversion"]) == 1.0


def test_pass_completion_by_team(events: pd.DataFrame) -> None:
    """Passaggi tentati, riusciti e percentuale per squadra."""
    completion = basic.pass_completion(events)
    assert int(completion.loc["1", "passes"]) == 3
    assert int(completion.loc["1", "completed"]) == 2
    assert round(float(completion.loc["1", "completion_pct"]), 2) == 66.67
    assert float(completion.loc["2", "completion_pct"]) == 100.0


def test_possession_by_events_declares_its_basis(events: pd.DataFrame) -> None:
    """Il possesso su base eventi è 80/20 e dichiara la base usata."""
    possession = basic.possession(events, basis="events")
    assert float(possession.loc["1", "possession_pct"]) == 80.0
    assert float(possession.loc["2", "possession_pct"]) == 20.0
    assert set(possession["basis"]) == {"events"}


def test_possession_by_passes_uses_a_different_base(events: pd.DataFrame) -> None:
    """La base "passes" produce un numero diverso e lo dichiara."""
    possession = basic.possession(events, basis="passes")
    assert float(possession.loc["1", "possession_pct"]) == 60.0
    assert set(possession["basis"]) == {"passes"}


def test_possession_rejects_unknown_basis(events: pd.DataFrame) -> None:
    """Una base non ammessa è un errore."""
    with pytest.raises(OpenZoneError):
        basic.possession(events, basis="inventata")  # type: ignore[arg-type]


def test_possession_on_time_basis_is_not_approximated(events: pd.DataFrame) -> None:
    """Il possesso sul tempo dichiara di non essere ancora implementato."""
    with pytest.raises(NotImplementedError):
        basic.possession(events, basis="time")


def test_missing_columns_are_reported_clearly(events: pd.DataFrame) -> None:
    """Una tabella non standardizzata produce un errore che dice cosa manca."""
    with pytest.raises(OpenZoneError, match="family"):
        basic.shots(events.drop(columns=["family"]))


def test_metrics_not_yet_implemented_fail_explicitly(events: pd.DataFrame) -> None:
    """Key passes e assist non indovinano: dichiarano di non essere pronti."""
    with pytest.raises(NotImplementedError):
        basic.key_passes(events)
    with pytest.raises(NotImplementedError):
        basic.assists(events)


def test_summary_counts(events: pd.DataFrame) -> None:
    """Il riepilogo conta eventi, partite, squadre, tiri e gol."""
    summary = basic.summary(events)
    assert summary == {"events": 10, "matches": 1, "teams": 2, "shots": 2, "goals": 1}
