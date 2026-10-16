"""Metriche calcistiche, organizzate per generazione.

La divisione in tre file rispecchia la maturità delle metriche, non la loro difficoltà
di calcolo:

* :mod:`~openzone.metrics.basic` — 1ª generazione: conteggi ricavabili direttamente
  dagli eventi standardizzati, senza modello;
* :mod:`~openzone.metrics.advanced` — 2ª generazione: qualità del singolo evento
  (xG, xA, xGOT, big chances), dove ogni numero dipende da un modello e va dichiarato;
* :mod:`~openzone.metrics.predictive` — 3ª generazione: valore delle azioni in
  sequenza e contesto spaziale (xT, PPDA, progressive passes/carries, packing);
* :mod:`~openzone.metrics.socceraction` — metriche calcolate su azioni SPADL
  (VAEP, xT basato su azioni).

Regola trasversale: una metrica che non è calcolabile con i dati disponibili solleva
un errore esplicito, oppure restituisce una colonna vuota con un avviso. Non
restituisce mai un'approssimazione silenziosa, perché un numero sbagliato con
l'aspetto di un numero giusto è il danno peggiore che una libreria di analisi possa
fare.

Example:
    >>> import openzone.metrics as metrics
    >>> metrics.available()
    {'basic': True, 'advanced': False, 'predictive': False, 'socceraction': False}
"""

from __future__ import annotations

from openzone._deps import has

__all__ = ["available", "basic", "predictive", "socceraction"]

#: Stato di implementazione di ciascun gruppo di metriche, aggiornato a mano insieme
#: alla roadmap: ``True`` solo quando le funzioni del modulo sono utilizzabili.
_IMPLEMENTED: dict[str, bool] = {
    "basic": True,
    "advanced": False,
    "predictive": False,
    "socceraction": False,
}


def available() -> dict[str, bool]:
    """Riporta lo stato di implementazione dei gruppi di metriche.

    Returns:
        Mappa ``{gruppo: implementato}``.

    Example:
        >>> available()["basic"]
        True
    """
    return dict(_IMPLEMENTED)


def dependencies(name: str) -> tuple[str, ...]:
    """Elenca le dipendenze opzionali che un gruppo di metriche richiede.

    Args:
        name: Nome del gruppo (``"basic"``, ``"advanced"``, ``"predictive"``,
            ``"socceraction"``).

    Returns:
        Nomi dei moduli opzionali necessari.

    Raises:
        KeyError: Se il gruppo non esiste.
    """
    required: dict[str, tuple[str, ...]] = {
        "basic": (),
        "advanced": (),
        "predictive": (),
        "socceraction": ("socceraction",),
    }
    if name not in required:
        known = ", ".join(sorted(required))
        raise KeyError(f"Gruppo di metriche sconosciuto: {name!r}. Gruppi noti: {known}")
    return required[name]


def dependencies_satisfied(name: str) -> bool:
    """Verifica se le dipendenze di un gruppo di metriche sono installate.

    Args:
        name: Nome del gruppo.

    Returns:
        ``True`` se tutte le dipendenze opzionali sono disponibili.
    """
    return all(has(module) for module in dependencies(name))


def __getattr__(name: str) -> object:
    """Importa i sottomoduli di metriche su richiesta.

    Args:
        name: Nome del sottomodulo.

    Returns:
        Il modulo richiesto.

    Raises:
        AttributeError: Se il nome non è un sottomodulo noto.
    """
    if name in {"basic", "advanced", "predictive", "socceraction"}:
        from importlib import import_module

        return import_module(f"openzone.metrics.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Elenca gli attributi del modulo, inclusi i sottomoduli pigri."""
    return sorted({*globals(), "advanced", "basic", "predictive", "socceraction"})
