"""Modelli: possesso, clustering delle azioni, simulazione.

Questo modulo contiene le parti di OpenZone che *stimano* qualcosa invece di misurarlo:
ricostruire chi ha il possesso, raggruppare azioni simili, simulare scenari. Sono
componenti con vita propria, che consumano l'output degli altri moduli e non li
modificano.

Sono anche i moduli con le dipendenze più pesanti (``scikit-learn`` per il clustering) e
per questo sono tenuti in un extra separato: chi vuole solo le metriche non li installa.

Example:
    >>> from openzone import models
    >>> models.available()["clustering"]
    False
"""

from __future__ import annotations

from openzone._deps import has

__all__ = ["available"]


def available() -> dict[str, bool]:
    """Riporta lo stato di implementazione dei modelli e delle loro dipendenze.

    ``dependencies`` riporta a parte la disponibilità di ``scikit-learn``: un modello
    non implementato resta non disponibile anche quando le sue dipendenze ci sono, e
    confondere le due cose renderebbe il report inutile.

    Returns:
        Mappa ``{nome: pronto}`` più la chiave ``dependencies``.
    """
    return {
        "possession": False,
        "clustering": False,
        "simulation": False,
        "dependencies": has("sklearn"),
    }
