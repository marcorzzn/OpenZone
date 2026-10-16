"""Test del glossario: metriche, fonti, definizioni Opta."""

from __future__ import annotations

import pytest

from openzone.exceptions import MetricNotFoundError
from openzone.glossary import (
    _store,
    aliases_index,
    format_glossary,
    generation_of,
    get_glossary,
    metric_names,
    metrics,
    opta_event_type,
    opta_event_types,
    opta_qualifiers,
    source,
    source_names,
    sources,
)


@pytest.fixture(autouse=True)
def _fresh_cache() -> None:
    """Svuota la cache dei file YAML prima di ogni test del glossario."""
    _store.clear_cache()


def test_all_blueprint_metrics_are_documented() -> None:
    """Ogni metrica citata nel blueprint ha una scheda nel glossario."""
    expected = {
        "xg",
        "xa",
        "xgot",
        "ipo",
        "xt",
        "ppda",
        "progressive_passes",
        "packing",
        "pitch_control",
        "big_chances",
    }
    assert expected <= set(metric_names())


def test_get_glossary_is_case_insensitive_and_accepts_aliases() -> None:
    """La ricerca ignora maiuscole e accetta gli alias."""
    assert get_glossary("XG")["key"] == "xg"
    assert get_glossary("expected threat")["key"] == "xt"
    assert get_glossary("expected-goals")["key"] == "xg"


def test_get_glossary_unknown_metric_suggests_alternatives() -> None:
    """Una metrica sconosciuta fallisce indicando i nomi simili."""
    with pytest.raises(MetricNotFoundError) as excinfo:
        get_glossary("xg2")
    assert excinfo.value.suggestions
    assert "xg" in excinfo.value.suggestions


def test_generation_of_matches_glossary() -> None:
    """La generazione è quella dichiarata nella scheda."""
    assert generation_of("goals") == 1
    assert generation_of("xG") == 2
    assert generation_of("ppda") == 3


def test_every_metric_declares_required_fields() -> None:
    """Ogni scheda dichiara i campi minimi, incluso lo stato di calcolabilità."""
    allowed = {"yes", "partial", "external"}
    for key, entry in metrics().items():
        for field in ("name", "generation", "definition", "source", "computable"):
            assert field in entry, f"{key}: campo mancante {field}"
        assert entry["computable"] in allowed, f"{key}: computable non valido"
        assert isinstance(entry["generation"], int)


def test_proprietary_metric_is_not_claimed_as_computable() -> None:
    """L'IPO è dichiarato non calcolabile, con la motivazione."""
    entry = get_glossary("ipo")
    assert entry["computable"] == "external"
    assert entry["compute_with"] is None
    assert "proprietaria" in entry["notes"]


def test_aliases_index_maps_to_canonical_keys() -> None:
    """L'indice degli alias punta alle chiavi canoniche."""
    index = aliases_index()
    assert index["xt"] == "xt"
    assert index["expected_threat"] == "xt"


def test_format_glossary_is_readable() -> None:
    """La scheda formattata contiene nome, generazione e fonti."""
    text = format_glossary("ppda")
    assert "Passes Per Defensive Action" in text
    assert "generazione: 3" in text
    assert "opta" in text


def test_sources_are_documented_with_licence_and_adapter() -> None:
    """Ogni fonte dichiara licenza, stato della licenza e ridistribuibilità."""
    for key, entry in sources().items():
        for field in ("name", "kind", "license", "license_status", "redistributable"):
            assert field in entry, f"{key}: campo mancante {field}"
        assert entry["license_status"] in {"declared", "uncertain", "proprietary"}
        assert isinstance(entry["redistributable"], bool)


def test_no_third_party_data_is_marked_redistributable_except_methods() -> None:
    """Nessuna fonte di dati di terze parti è contrassegnata come ridistribuibile."""
    for key, entry in sources().items():
        if entry["kind"] in {"event_data", "tracking_data", "shotmap", "aggregate_stats"}:
            assert entry["redistributable"] is False, key


def test_source_registry_and_lookup() -> None:
    """Le fonti note si interrogano per chiave."""
    assert "statsbomb_open_data" in source_names()
    assert source("statsbomb_open_data")["adapter"] == "openzone.ingest.statsbomb"
    with pytest.raises(KeyError):
        source("fonte_inesistente")


def test_redistribution_ban_is_documented_for_scraping_sources() -> None:
    """Le fonti che vietano lo scraping lo dichiarano nella scheda."""
    assert "vietano lo scraping" in source("sofascore")["scraping"]
    assert "vietano lo scraping" in source("whoscored")["scraping"]


def test_opta_event_types_are_flagged_unverified() -> None:
    """I tipi evento Opta sono incompleti e dichiarati non verificati."""
    types = opta_event_types()
    assert types[16]["name"] == "Goal"
    assert types[16]["is_goal"] is True
    assert types[13]["is_shot"] is True
    assert all(entry["verified"] is False for entry in types.values())


def test_opta_event_type_lookup_and_missing() -> None:
    """Un tipo non mappato fallisce senza indovinare."""
    assert opta_event_type(1)["name"] == "Pass"
    with pytest.raises(KeyError):
        opta_event_type(9999)


def test_opta_qualifiers_placeholder_is_documented() -> None:
    """I qualificatori noti sono pochi e marcati come non verificati."""
    qualifiers = opta_qualifiers()
    assert 140 in qualifiers
    assert qualifiers[140]["verified"] is False
