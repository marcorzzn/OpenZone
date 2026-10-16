"""Superficie pubblica di OpenZone.

Tutto ciò che un'applicazione esterna (per esempio il cruscotto OpenPitch) dovrebbe
usare passa da qui. La regola è netta:

* **questa è l'API stabile**: i nomi e le firme di questo modulo cambiano solo con un
  aumento di versione maggiore, e un cambio viene prima deprecato;
* **i sottomoduli sono interni**: :mod:`openzone.metrics`, :mod:`openzone.spatial` e
  simili possono cambiare fra versioni minori. Un'applicazione che li importa
  direttamente si assume il costo di seguirne l'evoluzione.

Questa separazione esiste perché OpenPitch deve poter fissare una versione di OpenZone e
aggiornarla quando vuole, non quando OpenZone cambia idea su un nome.

Example:
    >>> from openzone.api import get_glossary
    >>> get_glossary("xT")["generation"]
    3
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openzone.glossary import get_glossary as _get_glossary

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

__all__ = [
    "API_STABILITY",
    "compute_xg",
    "compute_xt",
    "get_glossary",
    "load_events",
    "load_shots",
    "plot_shot_map",
]

#: Descrizione del contratto di stabilità di questo modulo.
API_STABILITY = (
    "Superficie pubblica stabile: i nomi di openzone.api cambiano solo con una "
    "versione maggiore, previa deprecazione. I sottomoduli sono interni."
)


def get_glossary(metric: str) -> dict[str, Any]:
    """Restituisce definizione, formula, fonte e generazione di una metrica.

    Args:
        metric: Chiave o alias della metrica (``"xG"``, ``"expected threat"``, ...).

    Returns:
        La scheda della metrica, con la chiave canonica in ``"key"``.

    Raises:
        MetricNotFoundError: Se la metrica non è nel glossario, con i nomi simili fra
            i quali scegliere.

    Example:
        >>> get_glossary("ppda")["unit"]
        'rapporto'
    """
    return _get_glossary(metric)


def load_shots(player_id: int, season: str, **kwargs: Any) -> pd.DataFrame:
    """Restituisce tutti i tiri di un giocatore in una stagione.

    Args:
        player_id: Identificativo del giocatore.
        season: Stagione nel formato della fonte (per esempio ``"2024"``).
        **kwargs: Selezione della fonte, del campionato e della cache.

    Returns:
        DataFrame dei tiri, con una riga per tiro.

    Raises:
        NotImplementedError: L'accesso ai dati richiede prima la pipeline di ingestione
            e standardizzazione (Fase 1). La firma è congelata perché è il contratto che
            OpenPitch usa.
    """
    _ = (player_id, season, kwargs)
    raise NotImplementedError(
        "api.load_shots: richiede la pipeline di ingestione e standardizzazione della "
        "Fase 1 (vedi OPENZONE_BLUEPRINT.md §8)."
    )


def load_events(match_id: int, **kwargs: Any) -> pd.DataFrame:
    """Restituisce tutti gli eventi standardizzati di una partita.

    Args:
        match_id: Identificativo della partita.
        **kwargs: Selezione della fonte e della cache.

    Returns:
        DataFrame conforme a :data:`openzone.standardize.CANONICAL_EVENT_SCHEMA`.

    Raises:
        NotImplementedError: Previsto in Fase 1, insieme alla standardizzazione.
    """
    _ = (match_id, kwargs)
    raise NotImplementedError(
        "api.load_events: previsto in Fase 1, insieme alla pipeline di standardizzazione."
    )


def compute_xg(shots: pd.DataFrame, **kwargs: Any) -> pd.Series:
    """Calcola l'xG per ogni tiro.

    Args:
        shots: Tabella dei tiri standardizzati.
        **kwargs: Modello da usare e feature aggiuntive.

    Returns:
        Serie con l'xG calcolato, allineata a ``shots``.

    Raises:
        NotImplementedError: Il modello è previsto in Fase 2. Per usare l'xG già fornito
            dalla fonte, usa :func:`openzone.metrics.advanced.source_xg`.
    """
    from openzone.metrics import advanced

    return advanced.compute_xg(shots, **kwargs)


def compute_xt(events: pd.DataFrame, **kwargs: Any) -> pd.Series:
    """Calcola l'xT per ogni evento.

    Args:
        events: Eventi standardizzati.
        **kwargs: Parametri del modello (griglia, dataset di addestramento).

    Returns:
        Serie con il valore xT per evento.

    Raises:
        NotImplementedError: La matrice di transizione va addestrata e validata:
            previsto in Fase 2-3.
    """
    from openzone.metrics import predictive

    return predictive.compute_xt(events, **kwargs)


def plot_shot_map(shots: pd.DataFrame, **kwargs: Any) -> Any:
    """Disegna una mappa di tiro e restituisce figura e asse.

    Args:
        shots: Tabella dei tiri standardizzati.
        **kwargs: Argomenti passati a :func:`openzone.viz.shots.shot_map`.

    Returns:
        Coppia ``(figura, asse)``.

    Raises:
        NotImplementedError: Previsto in Fase 4, insieme al modulo di visualizzazione.
    """
    from openzone.viz import shots as shots_viz

    return shots_viz.shot_map(shots, **kwargs)
