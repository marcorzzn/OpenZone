"""Diagnostica dell'ambiente e verifica di integrità di OpenZone.

Serve a rispondere in un colpo solo alla domanda "in questo ambiente cosa funziona?":
quali dipendenze opzionali sono installate, quali moduli si importano, se i file del
glossario e ``pyproject.toml`` sono coerenti, e se le parti implementate producono i
numeri attesi su una fixture minima.

Non sostituisce ``pytest``: la suite in ``tests/`` è la verifica vera, con i suoi casi
limite. Questo script esiste per gli ambienti dove ``pytest`` non è installabile — per
esempio una macchina senza accesso a PyPI — e per la diagnosi rapida quando qualcosa non
torna.

Uso::

    python scripts/selfcheck.py
    python scripts/selfcheck.py --quiet

Il codice di uscita è 0 se tutti i controlli obbligatori passano, 1 altrimenti.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

#: Sottomoduli che devono essere importabili: se uno fallisce, il package è rotto.
SUBMODULES: tuple[str, ...] = (
    "openzone",
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
    "openzone.warehouse.duckdb",
)

#: File del glossario che devono esistere e non contenere tabulazioni.
GLOSSARY_FILES: tuple[str, ...] = (
    "openzone/glossary/metrics.yaml",
    "openzone/glossary/sources.yaml",
    "openzone/glossary/opta_definitions.yaml",
)

_results: list[tuple[bool, str]] = []

#: Se ``True``, ogni controllo stampa il proprio esito mentre viene eseguito.
_verbose = True


def check(condition: bool, description: str) -> bool:
    """Registra l'esito di un controllo.

    Args:
        condition: Esito del controllo.
        description: Descrizione leggibile del controllo.

    Returns:
        Lo stesso valore di ``condition``, per poterlo usare in catena.
    """
    ok = bool(condition)
    _results.append((ok, description))
    if _verbose:
        print(f"  [{'ok' if ok else '!!'}] {description}")
    return ok


def section(title: str) -> None:
    """Stampa il titolo di una sezione.

    Args:
        title: Titolo della sezione.
    """
    print(f"\n== {title} ==")


def report_python() -> None:
    """Stampa versione e percorso dell'interprete in uso."""
    section("Interprete")
    print(f"{sys.version.split()[0]} — {sys.executable}")
    check(sys.version_info >= (3, 10), "Python >= 3.10")


def report_dependencies() -> None:
    """Stampa la disponibilità di ogni dipendenza opzionale nota."""
    section("Dipendenze opzionali")
    try:
        from openzone import _deps
    except Exception as exc:  # noqa: BLE001 - diagnosi: qualunque errore va mostrato
        check(False, f"import di openzone._deps: {exc}")
        return
    for name, state in _deps.as_table().items():
        marker = "ok" if state["installed"] else "--"
        extra = state["extra"] or "(core)"
        print(f"  [{marker}] {name:<16} extra: {extra}")
    check(True, "tabella delle dipendenze leggibile")


def report_imports() -> None:
    """Verifica che ogni sottomodulo si importi."""
    section("Import dei moduli")
    failures: list[str] = []
    for name in SUBMODULES:
        try:
            importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - diagnosi: qualunque errore va mostrato
            failures.append(f"{name}: {type(exc).__name__}: {exc}")
    for failure in failures:
        print(f"  [!!] {failure}")
    check(not failures, f"tutti i {len(SUBMODULES)} sottomoduli si importano")


def report_pyproject() -> None:
    """Verifica che ``pyproject.toml`` sia TOML valido e dichiari il package."""
    section("pyproject.toml")
    path = REPO_ROOT / "pyproject.toml"
    if not check(path.is_file(), "pyproject.toml presente"):
        return
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
        print("  tomllib non disponibile: controllo saltato")
        return
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - diagnosi
        check(False, f"pyproject.toml non è TOML valido: {exc}")
        return
    project = data.get("project", {})
    check(project.get("name") == "openzone", "nome del progetto: openzone")
    check(bool(project.get("dependencies")), "dipendenze core dichiarate")
    extras = project.get("optional-dependencies", {})
    for extra in ("ingest", "standardize", "warehouse", "spatial", "viz", "models", "dev"):
        check(extra in extras, f"extra dichiarato: {extra}")


def report_glossary_files() -> None:
    """Verifica i file del glossario con controlli strutturali, senza YAML.

    Non è un parser YAML: verifica le proprietà che si rompono davvero (tabulazioni,
    file vuoto, chiavi di primo livello duplicate). La validazione sintattica completa
    richiede PyYAML ed è compito della suite di test.
    """
    section("File del glossario")
    for relative in GLOSSARY_FILES:
        path = REPO_ROOT / relative
        if not check(path.is_file(), f"{relative} presente"):
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        check(bool(text.strip()), f"{relative} non vuoto")
        tabbed = [index + 1 for index, line in enumerate(lines) if "\t" in line]
        tab_description = f"{relative} senza tabulazioni"
        if tabbed:
            tab_description += f" (trovate alle righe {tabbed})"
        check(not tabbed, tab_description)
        keys = [
            line.split(":")[0]
            for line in lines
            if line and not line.startswith((" ", "#", "-")) and line.rstrip().endswith(":")
        ]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        check(not duplicates, f"{relative} senza chiavi di primo livello duplicate")


def report_functional() -> None:
    """Esegue le parti implementate su una fixture minima e verifica i numeri.

    Richiede ``pandas``. Se manca, il controllo è segnalato come non eseguito.
    """
    section("Controllo funzionale")
    try:
        import pandas as pd
    except ModuleNotFoundError:
        print("  pandas assente: controllo funzionale non eseguito")
        check(True, "controllo funzionale saltato (pandas assente)")
        return

    from openzone.metrics import basic, predictive
    from openzone.spatial import half_spaces, pressing_zones
    from openzone.standardize.mapping import canonical_family, convert_coordinates
    from openzone.warehouse import Cache

    events = pd.DataFrame(
        {
            "event_id": ["e1", "e2", "e3", "e4", "e5", "e6"],
            "match_id": ["m1"] * 6,
            "family": ["pass", "pass", "carry", "shot", "pass", "defensive"],
            "type_name": ["Pass", "Pass", "Carry", "Goal", "Pass", "Interception"],
            "player_id": ["p1", "p2", "p2", "p4", "p5", "p6"],
            "team_id": ["1", "1", "1", "1", "2", "1"],
            "x": [30.0, 45.0, 60.0, 85.0, 90.0, 85.0],
            "y": [50.0, 50.0, 40.0, 50.0, 30.0, 60.0],
            "end_x": [45.0, 60.0, 75.0, 100.0, 85.0, None],
            "end_y": [50.0, 40.0, 45.0, 50.0, 30.0, None],
            "outcome": [True, True, True, True, True, True],
        }
    )

    coordinates = convert_coordinates(120.0, 80.0, "statsbomb", "opta")
    check(coordinates == (100.0, 100.0), "conversione coordinate")
    check(canonical_family("opta", 16) == "shot", "famiglia evento Opta 16")
    check(len(basic.shots(events)) == 1, "conteggio tiri")
    check(len(basic.goals(events)) == 1, "conteggio gol")
    possession = basic.possession(events, basis="events")
    check(round(float(possession.loc["1", "possession_pct"]), 2) == 83.33, "possesso")
    progressive = predictive.progressive_passes(events, threshold_m=10.0)
    check(set(progressive["event_id"]) == {"e1", "e2"}, "passaggi progressivi")
    ppda = predictive.compute_ppda(events, team_id="1")
    check(ppda.opponent_passes == 1 and ppda.defensive_actions == 1, "PPDA: conteggi")
    check(ppda.value == 1.0, "PPDA: valore")
    classified = half_spaces.classify(events)
    check(
        classified.loc[classified["event_id"] == "e4", "zone"].iloc[0] == "final_third_centre",
        "classificazione a zone",
    )
    band = pressing_zones.ppda_by_band(events, team_id="1")
    check("80-100" in set(band["band"]), "PPDA per fascia")

    # Non si usa tempfile: su Windows crea la directory con permessi ristretti
    # (0o700), che in un ambiente confinato tolgono l'accesso al processo stesso alla
    # directory appena creata. Una directory normale, creata e rimossa a mano, evita
    # il problema e rende il controllo eseguibile anche in sandbox.
    scratch = REPO_ROOT / ".selfcheck-scratch"
    try:
        scratch.mkdir(parents=True, exist_ok=True)
        cache = Cache(root=scratch, namespace="selfcheck")
        key = cache.key("eventi", match_id="m1")
        cache.put(key, events, match_id="m1")
        restored = cache.get(key)
        check(restored is not None and len(restored) == len(events), "cache: andata e ritorno")
        check(cache.delete(key) is True, "cache: cancellazione")
    except OSError as exc:
        print(f"  [--] controllo della cache non eseguito: {exc}")
        check(True, "controllo della cache saltato (permessi dell'ambiente)")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def main() -> int:
    """Esegue tutti i controlli e restituisce il codice di uscita.

    Returns:
        0 se nessun controllo obbligatorio è fallito, 1 altrimenti.
    """
    global _verbose

    parser = argparse.ArgumentParser(description="Diagnostica dell'ambiente OpenZone.")
    parser.add_argument("--quiet", action="store_true", help="stampa solo il riepilogo")
    args = parser.parse_args()
    _verbose = not args.quiet

    report_python()
    report_dependencies()
    report_imports()
    report_pyproject()
    report_glossary_files()
    report_functional()

    failed = [description for ok, description in _results if not ok]
    section("Riepilogo")
    print(f"  controlli: {len(_results)}   falliti: {len(failed)}")
    for description in failed:
        print(f"  [!!] {description}")
    if failed:
        print("\nNota: le dipendenze opzionali assenti non sono un errore.")
        return 1
    print("  tutto a posto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
