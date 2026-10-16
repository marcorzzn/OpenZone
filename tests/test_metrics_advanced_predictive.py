"""Test delle metriche di 2ª e 3ª generazione."""

from __future__ import annotations

import pandas as pd
import pytest

from openzone.exceptions import OpenZoneError
from openzone.metrics import advanced, predictive


def test_source_xg_is_read_from_the_source_column(shots: pd.DataFrame) -> None:
    """L'xG della fonte viene letto senza ricalcoli."""
    xg = advanced.source_xg(shots)
    assert list(xg) == [0.42, 0.11]
    assert float(xg.sum()) == pytest.approx(0.53)


def test_source_xg_accepts_an_explicit_column(shots: pd.DataFrame) -> None:
    """Si può indicare esplicitamente la colonna da usare."""
    renamed = shots.rename(columns={"xg": "my_xg"})
    assert float(advanced.source_xg(renamed, column="my_xg").sum()) == pytest.approx(0.53)


def test_source_xg_fails_when_the_source_has_no_xg(events: pd.DataFrame) -> None:
    """Se la fonte non fornisce xG, la funzione lo dice invece di inventare zeri."""
    shots_without_xg = events.loc[events["family"] == "shot"]
    with pytest.raises(OpenZoneError, match="Nessuna colonna di xG"):
        advanced.source_xg(shots_without_xg)


def test_xg_model_is_not_faked(shots: pd.DataFrame) -> None:
    """Il modello xG proprio dichiara di non essere ancora implementato."""
    with pytest.raises(NotImplementedError):
        advanced.compute_xg(shots)


def test_xgot_requires_post_shot_data(shots: pd.DataFrame) -> None:
    """Senza coordinate post-shot l'xGOT è un errore, non un'approssimazione."""
    with pytest.raises(OpenZoneError, match="xGOT non calcolabile"):
        advanced.compute_xgot(shots)


def test_xgot_reaches_the_model_when_data_is_present(shots: pd.DataFrame) -> None:
    """Con i dati post-shot si arriva al modello, che dichiara di non essere pronto."""
    with_post_shot = shots.assign(shot_end_x=100.0, shot_end_y=50.0)
    with pytest.raises(NotImplementedError):
        advanced.compute_xgot(with_post_shot)


def test_progression_metres_sign() -> None:
    """L'avanzamento è positivo verso la porta e negativo all'indietro."""
    assert predictive.progression_metres(30.0, 45.0) == 15.0
    assert predictive.progression_metres(45.0, 30.0) == -15.0


def test_progressive_passes_respect_the_threshold(events: pd.DataFrame) -> None:
    """Con soglia 10 m passano i due passaggi avanti, non quello indietro."""
    progressive = predictive.progressive_passes(events, threshold_m=10.0)
    assert set(progressive["event_id"]) == {"e1", "e2"}
    assert set(progressive["threshold_m"]) == {10.0}


def test_progressive_passes_threshold_is_parametric(events: pd.DataFrame) -> None:
    """Alzando la soglia resta solo il passaggio più lungo."""
    progressive = predictive.progressive_passes(events, threshold_m=16.0)
    assert set(progressive["event_id"]) == set()


def test_progressive_passes_excludes_failed_passes(events: pd.DataFrame) -> None:
    """Un passaggio sbagliato in avanti non conta come progressivo."""
    failed = events.copy()
    failed.loc[failed["event_id"] == "e1", "outcome"] = False
    progressive = predictive.progressive_passes(failed, threshold_m=10.0)
    assert set(progressive["event_id"]) == {"e2"}


def test_progressive_carries_use_the_carry_family(events: pd.DataFrame) -> None:
    """Le conduzioni progressive si contano sulla famiglia ``carry``."""
    carries = predictive.progressive_carries(events, threshold_m=10.0)
    assert set(carries["event_id"]) == {"e4"}


def test_progression_requires_coordinates(events: pd.DataFrame) -> None:
    """Senza coordinate di arrivo la metrica lo dice, invece di restituire zero."""
    with pytest.raises(OpenZoneError, match="end_x"):
        predictive.progressive_passes(events.drop(columns=["end_x"]))


def test_ppda_on_the_fixture(events: pd.DataFrame) -> None:
    """Il PPDA conta passaggi avversari e azioni difensive nella stessa zona."""
    result = predictive.compute_ppda(events, team_id="1")
    assert result.opponent_passes == 2
    assert result.defensive_actions == 2
    assert result.value == pytest.approx(1.0)
    assert result.pressing_height == predictive.DEFAULT_PRESSING_HEIGHT
    assert "defensive" in result.action_families


def test_ppda_returns_none_when_there_are_no_defensive_actions(events: pd.DataFrame) -> None:
    """Senza azioni difensive il rapporto non esiste: ``None``, non zero o infinito."""
    result = predictive.compute_ppda(events, team_id="2")
    assert result.defensive_actions == 0
    assert result.value is None


def test_ppda_result_carries_its_parameters(events: pd.DataFrame) -> None:
    """Il risultato espone i parametri usati, per poterli citare nel report."""
    row = predictive.compute_ppda(events, team_id="1", pressing_height=0.2).as_row()
    assert row["pressing_height"] == 0.2
    assert row["action_families"] == "defensive,duel,foul"


def test_ppda_rejects_invalid_pressing_height(events: pd.DataFrame) -> None:
    """Una zona di pressing non valida è un errore."""
    with pytest.raises(ValueError):
        predictive.compute_ppda(events, team_id="1", pressing_height=0.0)
    with pytest.raises(ValueError):
        predictive.compute_ppda(events, team_id="1", pressing_height=1.5)


def test_xt_and_packing_are_not_faked(events: pd.DataFrame) -> None:
    """XT e packing dichiarano di non essere pronti invece di approssimare."""
    with pytest.raises(NotImplementedError):
        predictive.compute_xt(events)
    with pytest.raises(OpenZoneError):
        predictive.packing(events, pd.DataFrame())
    with pytest.raises(NotImplementedError):
        predictive.packing(events, pd.DataFrame({"event_id": ["e1"], "x": [50.0], "y": [50.0]}))
