"""Pitch control: chi controlla lo spazio.

Il modello di controllo del campo stima, per ogni punto del campo e per ogni istante,
quale squadra ha più probabilità di arrivare per prima sul pallone. È il fondamento
delle metriche spaziali più avanzate (dominant regions, TDA, packing pesato) e richiede
dati che l'event data non contiene:

* **tracking data** con posizioni di tutti i giocatori a frequenza elevata (10-25 Hz);
* **stime di velocità** per calcolare i tempi di arrivo, quindi una fase di filtraggio
  e smoothing, altrimenti il rumore di posizione domina il risultato;
* **un modello di arrivo**, per esempio il tempo di percorrenza con accelerazione
  limitata, che è un'assunzione da dichiarare.

Con i soli dati evento si può produrre una versione statica e grossolana, che assume
che ogni giocatore sia fermo nella sua ultima posizione nota. Quella versione è
etichettata ``method="static_event_approximation"`` e non va presentata come pitch
control: serve a visualizzare una struttura, non a misurare.

Example:
    >>> from openzone.spatial import pitch_control
    >>> pitch_control.available()
    False
"""

from __future__ import annotations

from typing import Any, Final

from openzone.exceptions import OpenZoneError

__all__ = [
    "DEFAULT_GRID",
    "METHODS",
    "available",
    "control_surface",
    "dominant_region",
]

#: Risoluzione predefinita della griglia di controllo, in celle per lato.
DEFAULT_GRID: Final[tuple[int, int]] = (50, 32)

#: Metodi ammessi e loro significato.
METHODS: Final[dict[str, str]] = {
    "tracking_spearman": "Modello su tracking data con tempi di arrivo stimati.",
    "static_event_approximation": (
        "Approssimazione statica su dati evento: i giocatori sono assunti fermi. "
        "Da etichettare come tale e non confrontabile con un modello su tracking."
    ),
}


def available() -> bool:
    """Indica se il pitch control è implementato.

    Returns:
        Sempre ``False``: il modello è previsto in Fase 3.
    """
    return False


def control_surface(
    tracking: Any,
    *,
    method: str = "tracking_spearman",
    grid: tuple[int, int] = DEFAULT_GRID,
    **kwargs: Any,
) -> Any:
    """Calcola la superficie di controllo per un istante o per una sequenza.

    Args:
        tracking: Posizioni dei giocatori, con timestamp e velocità stimate.
        method: Metodo di calcolo, fra quelli in :data:`METHODS`.
        grid: Risoluzione della griglia ``(colonne, righe)``.
        **kwargs: Parametri del modello (limiti di accelerazione, orizzonte temporale).

    Returns:
        La superficie di controllo come matrice o come tabella di celle.

    Raises:
        OpenZoneError: Se il metodo richiede tracking data e questi non sono forniti.
        NotImplementedError: Il modello è previsto in Fase 3.
    """
    if method not in METHODS:
        raise OpenZoneError(
            f"Metodo non riconosciuto: {method!r}. Ammessi: {', '.join(METHODS)}"
        )
    if tracking is None or len(tracking) == 0:
        raise OpenZoneError(
            "pitch_control richiede le posizioni dei giocatori. "
            "Con i soli eventi non è calcolabile: usa method="
            "'static_event_approximation' e dichiara l'approssimazione."
        )
    _ = (grid, kwargs)
    raise NotImplementedError(
        "spatial.pitch_control.control_surface: previsto in Fase 3. Serve un modello di "
        "tempo di arrivo e una fase di smoothing delle posizioni."
    )


def dominant_region(control: Any, **kwargs: Any) -> Any:
    """Estrae la regione dominata da ciascuna squadra dalla superficie di controllo.

    Args:
        control: Superficie di controllo prodotta da :func:`control_surface`.
        **kwargs: Parametri aggiuntivi (soglia di dominanza).

    Returns:
        La regione dominata, per squadra.

    Raises:
        NotImplementedError: Previsto in Fase 3, insieme a :func:`control_surface`.
    """
    _ = (control, kwargs)
    raise NotImplementedError("spatial.pitch_control.dominant_region: previsto in Fase 3.")
