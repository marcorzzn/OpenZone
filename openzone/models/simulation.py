"""Simulazione di partita.

Simulare scenari (cosa succede se questa squadra pressa più alto, o se questo giocatore
esce) è l'uso più delicato di un modello calcistico, perché il risultato è credibile
anche quando è sbagliato. Le regole di questo modulo sono quindi più severe del solito:

* ogni simulazione dichiara le assunzioni e i parametri stimati da dati, distinguendoli
  da quelli scelti a mano;
* ogni risultato è accompagnato da un intervallo, non da un numero singolo: una
  simulazione senza incertezza è una previsione travestita;
* nessun output di questo modulo va presentato come previsione di una partita reale.

Example:
    >>> from openzone.models import simulation
    >>> simulation.available()
    False
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

__all__ = ["available", "simulate_match"]

#: Numero predefinito di replicazioni di una simulazione.
DEFAULT_REPLICATIONS = 1000


def available() -> bool:
    """Indica se la simulazione è implementata.

    Returns:
        Sempre ``False``: prevista in Fase 3.
    """
    return False


def simulate_match(
    home_strength: Any,
    away_strength: Any,
    *,
    replications: int = DEFAULT_REPLICATIONS,
    seed: int | None = None,
    **assumptions: Any,
) -> pd.DataFrame:
    """Simula una partita a partire da parametri di forza delle due squadre.

    Args:
        home_strength: Parametri della squadra di casa (attacco, difesa, ritmo).
        away_strength: Parametri della squadra ospite.
        replications: Numero di replicazioni.
        seed: Seme del generatore casuale. Va sempre fissato: senza, due esecuzioni
            identiche danno risultati diversi e il confronto è impossibile.
        **assumptions: Assunzioni del modello, registrate nel risultato.

    Returns:
        DataFrame con la distribuzione dei risultati simulati e i quantili.

    Raises:
        NotImplementedError: Previsto in Fase 3.
    """
    _ = (home_strength, away_strength, replications, seed, assumptions)
    raise NotImplementedError(
        "models.simulation.simulate_match: previsto in Fase 3."
    )
