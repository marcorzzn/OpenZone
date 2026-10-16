"""Visualizzazione statica con ``mplsoccer``.

Grafici pronti per un report: mappe di tiro, reti di passaggio, frecce. Le funzioni
restituiscono la figura invece di salvarla, così chi le usa decide formato e
destinazione, e nei test si può verificare che la figura sia stata costruita senza
scrivere file.

Convenzioni comuni a tutte le funzioni:

* campo orientato con l'attacco verso destra, coordinate normalizzate 100x100, così i
  grafici sono confrontabili con i numeri delle metriche;
* ogni grafico che mostra un valore stimato riporta nel titolo la fonte o il modello che
  l'ha prodotto: un grafico è la forma più facile in cui un numero senza provenienza
  finisce in una presentazione;
* le funzioni non chiamano ``show()``.

Richiede l'extra ``viz`` (``mplsoccer``, ``matplotlib``).

Example:
    >>> from openzone import viz
    >>> viz.available()["mplsoccer"]
    False
"""

from __future__ import annotations

from openzone._deps import has

__all__ = ["PITCH_TYPE", "available"]

#: Tipo di campo predefinito per ``mplsoccer``.
PITCH_TYPE = "opta"


def available() -> dict[str, bool]:
    """Riporta la disponibilità delle dipendenze di visualizzazione.

    Returns:
        Mappa ``{"mplsoccer": bool, "matplotlib": bool}``.
    """
    return {"mplsoccer": has("mplsoccer"), "matplotlib": has("matplotlib")}
