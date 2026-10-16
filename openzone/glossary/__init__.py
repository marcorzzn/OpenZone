"""Glossario integrato: definizioni, formule, fonti e generazioni.

Questo modulo è l'enciclopedia interna di OpenZone. Ogni metrica calcolata dalla
libreria ha qui la sua scheda, con definizione, formula, unità di misura, fonte
originale e generazione di appartenenza. Ogni fonte dati ha la sua scheda con
licenza, modalità di accesso e limiti d'uso.

Le tre collezioni sono esposte con nomi espliciti, senza collisioni con le funzioni
pubbliche di :mod:`openzone.api`::

    from openzone.glossary import get_glossary, metrics, sources

    get_glossary("xT")["definition"]
    metrics()["xg"]["generation"]
    sources()["statsbomb_open_data"]["license"]

Example:
    >>> from openzone.glossary import metric_names
    >>> "xg" in metric_names()
    True
"""

from __future__ import annotations

import difflib
from typing import Any

from openzone.exceptions import MetricNotFoundError
from openzone.glossary import _store

__all__ = [
    "aliases_index",
    "format_glossary",
    "generation_of",
    "get_glossary",
    "metric_names",
    "metrics",
    "opta_event_type",
    "opta_event_types",
    "opta_qualifiers",
    "source",
    "source_names",
    "sources",
]


def _normalise(name: str) -> str:
    """Normalizza un nome di metrica per il confronto.

    Args:
        name: Nome fornito dall'utente, in qualunque forma.

    Returns:
        Il nome in minuscolo, senza spazi o trattini bassi ai bordi.
    """
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def metrics() -> dict[str, dict[str, Any]]:
    """Restituisce tutte le schede metrica del glossario.

    Returns:
        Mappa ``{chiave_metrica: scheda}``.
    """
    entries = _store.load_metrics().get("metrics") or {}
    return {str(key): dict(value) for key, value in entries.items()}


def metric_names() -> list[str]:
    """Elenca le chiavi canoniche delle metriche note, in ordine alfabetico.

    Returns:
        Lista di nomi canonici.
    """
    return sorted(metrics())


def aliases_index() -> dict[str, str]:
    """Costruisce l'indice degli alias verso le chiavi canoniche.

    Returns:
        Mappa ``{alias_normalizzato: chiave_canonica}``. La chiave canonica è
        indicizzata anche verso sé stessa.
    """
    index: dict[str, str] = {}
    for key, entry in metrics().items():
        index[_normalise(key)] = key
        for alias in entry.get("aliases") or []:
            index[_normalise(str(alias))] = key
    return index


def get_glossary(metric: str) -> dict[str, Any]:
    """Restituisce la scheda di una metrica: definizione, formula, fonte, generazione.

    La ricerca non distingue maiuscole/minuscole, ignora spazi e trattini e accetta
    gli alias registrati (per esempio ``"expected threat"`` per ``"xt"``).

    Args:
        metric: Chiave o alias della metrica.

    Returns:
        La scheda della metrica, con la chiave canonica in ``"key"``.

    Raises:
        MetricNotFoundError: Se la metrica non è nel glossario, con i nomi simili
            fra i quali l'utente può scegliere.

    Example:
        >>> get_glossary("xG")["generation"]
        2
    """
    index = aliases_index()
    normalised = _normalise(metric)
    key = index.get(normalised)
    if key is None:
        suggestions = difflib.get_close_matches(normalised, list(index), n=3, cutoff=0.6)
        raise MetricNotFoundError(metric, [index[item] for item in suggestions])
    entry = metrics()[key]
    entry["key"] = key
    return entry


def generation_of(metric: str) -> int:
    """Restituisce la generazione di una metrica (1ª, 2ª o 3ª).

    Args:
        metric: Chiave o alias della metrica.

    Returns:
        Il numero di generazione.

    Raises:
        MetricNotFoundError: Se la metrica non è nel glossario.
    """
    return int(get_glossary(metric)["generation"])


def format_glossary(metric: str) -> str:
    """Rende una scheda metrica come testo leggibile.

    Args:
        metric: Chiave o alias della metrica.

    Returns:
        Testo su più righe pronto per la stampa a terminale.

    Example:
        >>> print(format_glossary("ppda"))  # doctest: +SKIP
    """
    entry = get_glossary(metric)
    lines = [f"{entry.get('name', entry['key'])} ({entry['key']})"]
    lines.append(f"  generazione: {entry.get('generation')}")
    if entry.get("definition"):
        lines.append(f"  definizione: {' '.join(str(entry['definition']).split())}")
    if entry.get("formula"):
        lines.append(f"  formula: {' '.join(str(entry['formula']).split())}")
    if entry.get("unit"):
        lines.append(f"  unità: {entry['unit']}")
    if entry.get("source"):
        lines.append(f"  fonti: {', '.join(map(str, entry['source']))}")
    if entry.get("computable"):
        lines.append(f"  calcolabile in OpenZone: {entry['computable']}")
    if entry.get("notes"):
        lines.append(f"  note: {' '.join(str(entry['notes']).split())}")
    return "\n".join(lines)


def sources() -> dict[str, dict[str, Any]]:
    """Restituisce tutte le schede fonte del glossario.

    Returns:
        Mappa ``{chiave_fonte: scheda}``.
    """
    entries = _store.load_sources().get("sources") or {}
    return {str(key): dict(value) for key, value in entries.items()}


def source_names() -> list[str]:
    """Elenca le chiavi canoniche delle fonti note, in ordine alfabetico.

    Returns:
        Lista di nomi canonici.
    """
    return sorted(sources())


def source(name: str) -> dict[str, Any]:
    """Restituisce la scheda di una fonte dati.

    Args:
        name: Chiave canonica della fonte.

    Returns:
        La scheda della fonte, con la chiave in ``"key"``.

    Raises:
        KeyError: Se la fonte non è registrata, con i nomi simili come suggerimento.
    """
    entries = sources()
    key = _normalise(name)
    if key not in entries:
        suggestions = difflib.get_close_matches(key, list(entries), n=3, cutoff=0.6)
        raise KeyError(f"Fonte non registrata: {name!r}. Forse cercavi: {', '.join(suggestions)}")
    entry = entries[key]
    entry["key"] = key
    return entry


def opta_event_types() -> dict[int, dict[str, Any]]:
    """Restituisce i tipi evento Opta noti, indicizzati per ``type_id``.

    Returns:
        Mappa ``{type_id: {"name": str, "family": str, ...}}``.
    """
    entries = _store.load_opta_definitions().get("event_types") or {}
    return {int(key): dict(value) for key, value in entries.items()}


def opta_event_type(type_id: int) -> dict[str, Any]:
    """Restituisce la scheda di un tipo evento Opta.

    Args:
        type_id: Identificativo numerico del tipo evento.

    Returns:
        La scheda del tipo evento, con ``type_id`` incluso.

    Raises:
        KeyError: Se il ``type_id`` non è mappato.
    """
    entries = opta_event_types()
    if int(type_id) not in entries:
        raise KeyError(
            f"Tipo evento Opta non mappato: {type_id!r}. "
            "Aggiungilo a openzone/glossary/opta_definitions.yaml."
        )
    entry = entries[int(type_id)]
    entry["type_id"] = int(type_id)
    return entry


def opta_qualifiers() -> dict[int, dict[str, Any]]:
    """Restituisce i qualificatori Opta noti, indicizzati per ``qualifier_id``.

    Returns:
        Mappa ``{qualifier_id: {"name": str, "confidence": str}}``.
    """
    entries = _store.load_opta_definitions().get("qualifiers") or {}
    return {int(key): dict(value) for key, value in entries.items()}
