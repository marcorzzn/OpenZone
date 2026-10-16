"""Test della struttura del package e del caricamento dei moduli."""

from __future__ import annotations

import importlib
import subprocess
import sys

import pytest

import openzone

SUBMODULES = [
    "openzone.api",
    "openzone.exceptions",
    "openzone.glossary",
    "openzone.glossary._store",
    "openzone.ingest",
    "openzone.ingest.datahub",
    "openzone.ingest.football_data_org",
    "openzone.ingest.pannadata",
    "openzone.ingest.scraperfc",
    "openzone.ingest.soccerdata",
    "openzone.ingest.statsbomb",
    "openzone.ingest.understat",
    "openzone.ingest.whoscored",
    "openzone.metrics",
    "openzone.metrics.advanced",
    "openzone.metrics.basic",
    "openzone.metrics.predictive",
    "openzone.metrics.socceraction",
    "openzone.models",
    "openzone.models.clustering",
    "openzone.models.possession",
    "openzone.models.simulation",
    "openzone.spatial",
    "openzone.spatial.half_spaces",
    "openzone.spatial.pass_networks",
    "openzone.spatial.pitch_control",
    "openzone.spatial.pressing_zones",
    "openzone.spatial.triangles",
    "openzone.standardize",
    "openzone.standardize.kloppy",
    "openzone.standardize.mapping",
    "openzone.standardize.schema",
    "openzone.standardize.socceraction",
    "openzone.viz",
    "openzone.viz.passes",
    "openzone.viz.pitch",
    "openzone.viz.shots",
    "openzone.warehouse",
    "openzone.warehouse.cache",
]


def test_version_is_declared() -> None:
    """La versione del package è una stringa semantica."""
    assert openzone.__version__ == "0.1.0"


@pytest.mark.parametrize("module_name", SUBMODULES)
def test_submodule_imports(module_name: str) -> None:
    """Ogni sottomodulo dichiarato si importa senza errori."""
    assert importlib.import_module(module_name) is not None


def test_import_openzone_does_not_pull_heavy_dependencies() -> None:
    """``import openzone`` non carica dipendenze pesanti.

    Il controllo gira in un processo separato: dentro la sessione di pytest ``pandas`` è
    già in ``sys.modules`` e non si potrebbe distinguere chi l'ha importato.
    """
    code = (
        "import sys, openzone;"
        "heavy = [m for m in ('pandas', 'duckdb', 'mplsoccer', 'networkx', 'matplotlib')"
        " if m in sys.modules];"
        "assert not heavy, heavy;"
        "print(openzone.__version__)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == openzone.__version__


def test_lazy_api_attributes() -> None:
    """I nomi dell'API pubblica sono raggiungibili anche da ``openzone``."""
    assert callable(openzone.get_glossary)
    assert callable(openzone.load_events)


def test_unknown_attribute_raises() -> None:
    """Un attributo inesistente solleva ``AttributeError``."""
    with pytest.raises(AttributeError):
        _ = openzone.non_esiste


def test_dir_lists_lazy_exports() -> None:
    """``dir()`` include i nomi serviti pigramente."""
    assert {"get_glossary", "load_shots"} <= set(dir(openzone))


def test_py_typed_marker_is_packaged() -> None:
    """Il marker PEP 561 è presente accanto al codice."""
    from pathlib import Path

    assert (Path(openzone.__file__).parent / "py.typed").is_file()
