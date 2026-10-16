"""Test degli adapter di ingestione.

I test unitari non toccano la rete: verificano il registro degli adapter, la
disponibilità dichiarata e il comportamento in assenza di dipendenze. Il test che
scarica davvero da StatsBomb Open Data è marcato ``network`` ed è escluso dalla
esecuzione predefinita.
"""

from __future__ import annotations

import pandas as pd
import pytest

from openzone.exceptions import SourceNotAvailableError
from openzone.ingest import adapter, adapters, available_adapters, datahub, statsbomb


def test_registry_lists_the_blueprint_sources() -> None:
    """Il registro copre le fonti previste dal blueprint."""
    registered = adapters()
    assert {
        "statsbomb_open_data",
        "pannadata",
        "soccerdata",
        "scraperfc",
        "understat",
        "whoscored",
        "datahub",
        "football_data_org",
    } <= set(registered)


def test_adapter_for_unknown_source_fails_with_the_known_ones() -> None:
    """Una fonte senza adapter è un errore che elenca le fonti note."""
    with pytest.raises(KeyError) as excinfo:
        adapter("fonte_inesistente")
    assert "statsbomb_open_data" in str(excinfo.value)


def test_statsbomb_adapter_needs_no_credentials() -> None:
    """StatsBomb Open Data è utilizzabile senza chiavi API."""
    assert statsbomb.available() is True
    assert statsbomb.requires == ()


def test_available_adapters_excludes_missing_dependencies() -> None:
    """Sono pronti solo gli adapter le cui dipendenze sono installate."""
    ready = available_adapters()
    assert "statsbomb_open_data" in ready
    assert "datahub" in ready
    assert "soccerdata" not in ready


def test_datahub_requires_the_minimum_columns(tmp_path: object) -> None:
    """Un file senza le colonne minime viene rifiutato con un messaggio chiaro."""
    from pathlib import Path

    path = Path(str(tmp_path)) / "partite.csv"
    path.write_text("squadra_a,squadra_b\nInter,Milan\n", encoding="utf-8")
    with pytest.raises(SourceNotAvailableError, match="Colonne obbligatorie"):
        datahub.load_matches(path)


def test_datahub_reads_a_valid_file(tmp_path: object) -> None:
    """Un file valido viene letto e la provenienza resta allegata."""
    from pathlib import Path

    path = Path(str(tmp_path)) / "partite.csv"
    path.write_text(
        "date,home_team,away_team\n2024-08-17,Genoa,Inter\n",
        encoding="utf-8",
    )
    frame = datahub.load_matches(path)
    assert len(frame) == 1
    assert frame.attrs["openzone.source"] == "datahub"
    assert frame.attrs["openzone.path"] == str(path.resolve())


def test_datahub_rejects_unknown_extension(tmp_path: object) -> None:
    """Un'estensione non gestita è un errore esplicito."""
    from pathlib import Path

    path = Path(str(tmp_path)) / "partite.txt"
    path.write_text("date,home_team,away_team\n", encoding="utf-8")
    with pytest.raises(SourceNotAvailableError, match="Estensione non gestita"):
        datahub.load_matches(path)


def test_pannadata_refuses_to_download() -> None:
    """L'adapter Opta lavora solo su file locali: niente download automatico."""
    from openzone.ingest import pannadata

    with pytest.raises(SourceNotAvailableError, match="solo file locali"):
        pannadata.load_events("D:/percorso/inesistente.parquet")


@pytest.mark.network
def test_statsbomb_open_data_is_reachable() -> None:
    """StatsBomb Open Data risponde e contiene la Serie A 2015/16."""
    try:
        frame = statsbomb.competitions()
    except SourceNotAvailableError as exc:
        pytest.skip(f"rete non disponibile: {exc}")

    assert isinstance(frame, pd.DataFrame)
    serie_a = frame.loc[frame["competition_id"] == statsbomb.SERIE_A_COMPETITION_ID]
    assert not serie_a.empty
    assert (serie_a["season_id"] == statsbomb.SERIE_A_SEASON_ID).any()
