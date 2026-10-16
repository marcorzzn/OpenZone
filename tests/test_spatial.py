"""Test dell'analisi spaziale: zone, reti di passaggio, pressing per fascia."""

from __future__ import annotations

import pandas as pd
import pytest

from openzone.exceptions import OpenZoneError
from openzone.spatial import half_spaces, pass_networks, pressing_zones


def test_thirds_classification() -> None:
    """I terzi di campo seguono i limiti dichiarati."""
    assert half_spaces.classify_thirds(0.0) == "defensive_third"
    assert half_spaces.classify_thirds(30.0) == "defensive_third"
    assert half_spaces.classify_thirds(40.0) == "middle_third"
    assert half_spaces.classify_thirds(90.0) == "final_third"
    # 33,3 è appena sotto il confine esatto (100/3): resta nel primo terzo.
    assert half_spaces.classify_thirds(33.3) == "defensive_third"


def test_channel_classification_includes_half_spaces() -> None:
    """I cinque corridoi sono distinti e gli half-spaces sono riconosciuti."""
    assert half_spaces.classify_channels(10.0) == "left_wing"
    assert half_spaces.classify_channels(30.0) == "left_half_space"
    assert half_spaces.classify_channels(50.0) == "centre"
    assert half_spaces.classify_channels(70.0) == "right_half_space"
    assert half_spaces.classify_channels(90.0) == "right_wing"
    assert half_spaces.is_half_space(30.0) is True
    assert half_spaces.is_half_space(50.0) is False


def test_classify_adds_zone_columns(events: pd.DataFrame) -> None:
    """``classify`` aggiunge terzo, corridoio, half-space e zona."""
    classified = half_spaces.classify(events)
    assert {"third", "channel", "half_space", "zone"} <= set(classified.columns)
    goal = classified.loc[classified["event_id"] == "e5"].iloc[0]
    assert goal["third"] == "final_third"
    assert goal["channel"] == "centre"
    assert goal["zone"] == "final_third_centre"


def test_classify_leaves_missing_coordinates_missing(events: pd.DataFrame) -> None:
    """Un evento senza coordinate non finisce in una zona a caso."""
    partial = events.copy()
    partial.loc[partial["event_id"] == "e9", "x"] = None
    classified = half_spaces.classify(partial)
    row = classified.loc[classified["event_id"] == "e9"].iloc[0]
    assert row["zone"] is None
    assert row["third"] is None


def test_zone_counts_require_classification(events: pd.DataFrame) -> None:
    """Senza le colonne di zona il conteggio lo dice chiaramente."""
    with pytest.raises(OpenZoneError, match="classify"):
        half_spaces.zone_counts(events)
    counts = half_spaces.zone_counts(half_spaces.classify(events))
    assert int(counts["events"].sum()) == len(events)


def test_pass_edges_require_a_receiver(events: pd.DataFrame) -> None:
    """Senza il ricevente la rete fra giocatori non esiste e la funzione lo dichiara."""
    with pytest.raises(OpenZoneError, match="ricevente"):
        pass_networks.pass_edges(events.drop(columns=["receiver_id"]))


def test_pass_edges_builds_the_edge_list(events: pd.DataFrame) -> None:
    """Gli archi aggregati contano i passaggi riusciti fra coppie."""
    edges = pass_networks.pass_edges(events, team_id="1")
    pairs = set(zip(edges["passer_id"], edges["receiver_id"], strict=True))
    assert pairs == {("p1", "p2"), ("p2", "p3")}
    assert int(edges["passes"].sum()) == 2
    assert not (edges["passer_id"] == "p3").any()


def test_pass_edges_can_include_failed_passes(events: pd.DataFrame) -> None:
    """Includendo i passaggi sbagliati compare anche il terzo arco."""
    edges = pass_networks.pass_edges(events, team_id="1", completed_only=False)
    assert ("p3", "p2") in set(zip(edges["passer_id"], edges["receiver_id"], strict=True))
    assert int(edges["passes"].sum()) == 3


def test_pass_graph_requires_networkx(events: pd.DataFrame) -> None:
    """Il grafo richiede ``networkx``: senza, l'errore dice quale extra installare."""
    pytest.importorskip("networkx")
    edges = pass_networks.pass_edges(events, team_id="1")
    graph = pass_networks.to_graph(edges)
    assert graph.number_of_edges() == 2
    strength = pass_networks.node_strength(graph)
    assert int(strength.loc[strength["player_id"] == "p1", "passes_made"].iloc[0]) == 1


def test_ppda_by_band_uses_the_band_as_pressing_zone(events: pd.DataFrame) -> None:
    """Il PPDA per fascia conta solo ciò che accade dentro la fascia."""
    table = pressing_zones.ppda_by_band(events, team_id="1")
    assert list(table["band"]) == ["0-40", "40-60", "60-80", "80-100"]
    final_band = table.loc[table["band"] == "80-100"].iloc[0]
    assert int(final_band["opponent_passes"]) == 2
    assert int(final_band["defensive_actions"]) == 2
    assert float(final_band["ppda"]) == pytest.approx(1.0)
    empty_band = table.loc[table["band"] == "0-40"].iloc[0]
    # In un DataFrame un valore assente diventa NaN: ``compute_ppda`` restituisce
    # ``None``, la tabella lo rappresenta come nullo. Il test verifica l'assenza, non
    # lo zero.
    assert pd.isna(empty_band["ppda"])
    assert int(empty_band["events"]) > 0


def test_band_labels_are_generated_from_bounds() -> None:
    """Le etichette delle fasce derivano dai limiti, non da una lista duplicata."""
    assert pressing_zones.band_labels() == ["0-40", "40-60", "60-80", "80-100"]


def test_ppda_table_includes_overall_and_bands(events: pd.DataFrame) -> None:
    """La tabella per partita contiene sia il valore complessivo sia le fasce."""
    table = pressing_zones.ppda_table(events)
    match_rows = table.loc[table["band"] == "match"]
    assert set(match_rows["team_id"]) == {"1", "2"}
    assert set(table["band"]) == {"match", "0-40", "40-60", "60-80", "80-100"}


def test_ppda_table_requires_match_id(events: pd.DataFrame) -> None:
    """Senza ``match_id`` l'aggregazione per partita non è possibile."""
    with pytest.raises(OpenZoneError, match="match_id"):
        pressing_zones.ppda_table(events.drop(columns=["match_id"]))
