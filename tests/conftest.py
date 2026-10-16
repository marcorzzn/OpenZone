"""Fixture condivise dai test.

La fixture principale è una tabella di eventi nello schema canonico, costruita a mano e
volutamente piccola: i valori attesi sono calcolati a mente e verificabili leggendo il
test, cosa impossibile con un dataset reale di migliaia di righe. I test che usano dati
veri sono separati e marcati ``network``.

Layout della fixture (10 eventi, 1 partita, 2 squadre):

* squadra ``"1"``: 3 passaggi (2 riusciti), 1 conduzione, 2 tiri (1 gol), 1
  intercettazione, 1 fallo;
* squadra ``"2"``: 2 passaggi, entrambi riusciti vicino alla porta avversaria.

Serve a verificare conteggi, progressione, PPDA e zone con numeri che si possono
ricalcolare a mano.
"""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def events() -> pd.DataFrame:
    """Eventi canonici di una singola partita.

    Returns:
        DataFrame con 10 eventi conforme a ``CANONICAL_EVENT_SCHEMA``.
    """
    rows = [
        # event_id, period, minute, second, type_id, type_name, family, player, team,
        # x, y, end_x, end_y, outcome, receiver
        ("e1", 1, 1, 5, 1, "Pass", "pass", "p1", "1", 30.0, 50.0, 45.0, 50.0, True, "p2"),
        ("e2", 1, 1, 8, 1, "Pass", "pass", "p2", "1", 45.0, 50.0, 60.0, 40.0, True, "p3"),
        ("e3", 1, 1, 11, 1, "Pass", "pass", "p3", "1", 60.0, 40.0, 55.0, 45.0, False, "p2"),
        ("e4", 1, 1, 14, 43, "Carry", "carry", "p2", "1", 60.0, 40.0, 75.0, 45.0, True, None),
        ("e5", 1, 1, 18, 16, "Goal", "shot", "p4", "1", 85.0, 50.0, 100.0, 50.0, True, None),
        (
            "e6",
            1,
            1,
            22,
            15,
            "Attempt Saved",
            "shot",
            "p3",
            "1",
            80.0,
            45.0,
            95.0,
            48.0,
            True,
            None,
        ),
        ("e7", 1, 2, 4, 1, "Pass", "pass", "p5", "2", 90.0, 30.0, 85.0, 30.0, True, "p6"),
        ("e8", 1, 2, 7, 1, "Pass", "pass", "p5", "2", 85.0, 70.0, 80.0, 70.0, True, "p6"),
        (
            "e9",
            1,
            2,
            9,
            8,
            "Interception",
            "defensive",
            "p6",
            "1",
            85.0,
            60.0,
            None,
            None,
            True,
            None,
        ),
        ("e10", 1, 2, 12, 4, "Foul", "foul", "p7", "1", 88.0, 55.0, None, None, False, None),
    ]
    frame = pd.DataFrame(
        rows,
        columns=[
            "event_id",
            "period",
            "minute",
            "second",
            "type_id",
            "type_name",
            "family",
            "player_id",
            "team_id",
            "x",
            "y",
            "end_x",
            "end_y",
            "outcome",
            "receiver_id",
        ],
    )
    frame["match_id"] = "m1"
    frame["source"] = "fixture"
    frame["qualifiers"] = [{} for _ in range(len(frame))]
    return frame


@pytest.fixture
def shots(events: pd.DataFrame) -> pd.DataFrame:
    """Solo i tiri della fixture, con un xG fornito dalla fonte.

    Args:
        events: Eventi canonici.

    Returns:
        DataFrame dei tiri con la colonna ``xg``.
    """
    subset = events.loc[events["family"] == "shot"].copy()
    subset["xg"] = [0.42, 0.11]
    return subset
