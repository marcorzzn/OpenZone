"""Metriche calcolate su azioni SPADL: VAEP e xT basato su azioni.

Le metriche di questo modulo non si calcolano direttamente sui DataFrame di eventi: la
pipeline è eventi grezzi → SPADL → modello → valori per azione. Serve ``socceraction``
e un modello addestrato.

Perché è un modulo separato e non parte di :mod:`openzone.metrics.predictive`: perché
il valore restituito non è una proprietà dell'evento ma il risultato di un modello
addestrato su azioni, e mescolarlo con metriche definite geometricamente confonderebbe
due cose diverse.

Example:
    >>> from openzone.metrics import socceraction
    >>> socceraction.available()
    False
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openzone._deps import has, require

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

__all__ = ["available", "load_model", "train_vaep", "vaep", "xt_from_actions"]

#: Versione dei modelli preaddestrati distribuiti con ``socceraction``.
DEFAULT_MODEL_VERSION = "latest"


def available() -> bool:
    """Indica se le metriche SPADL sono utilizzabili.

    Returns:
        ``True`` se ``socceraction`` è installato.
    """
    return has("socceraction")


def load_model(name: str = "vaep", version: str = DEFAULT_MODEL_VERSION) -> Any:
    """Carica un modello preaddestrato fornito da ``socceraction``.

    Args:
        name: Nome del modello (``"vaep"`` o ``"xt"``).
        version: Versione dei pesi da scaricare.

    Returns:
        Coppia ``(modello, features)`` restituita da ``socceraction``.

    Raises:
        MissingDependencyError: Se ``socceraction`` non è installato.
        NotImplementedError: L'integrazione è prevista in Fase 2.
    """
    require("socceraction")
    _ = (name, version)
    raise NotImplementedError("metrics.socceraction.load_model: previsto in Fase 2.")


def train_vaep(actions: pd.DataFrame, **kwargs: Any) -> Any:
    """Addestra un modello VAEP su azioni SPADL.

    Args:
        actions: Azioni SPADL.
        **kwargs: Iperparametri del modello.

    Returns:
        Il modello addestrato, insieme alle feature usate.

    Raises:
        MissingDependencyError: Se ``socceraction`` non è installato.
        NotImplementedError: L'addestramento è previsto in Fase 2, con la validazione
            temporale (addestrare su stagioni passate e valutare su stagioni future).
    """
    require("socceraction")
    _ = (actions, kwargs)
    raise NotImplementedError(
        "metrics.socceraction.train_vaep: previsto in Fase 2, con split temporale e "
        "non casuale fra addestramento e valutazione."
    )


def vaep(actions: pd.DataFrame, model: Any | None = None, **kwargs: Any) -> pd.Series:
    """Calcola il valore VAEP di ogni azione SPADL.

    Args:
        actions: Azioni SPADL.
        model: Modello da usare; se omesso, si carica quello predefinito.
        **kwargs: Argomenti aggiuntivi.

    Returns:
        Serie con il valore VAEP per azione.

    Raises:
        MissingDependencyError: Se ``socceraction`` non è installato.
        NotImplementedError: Previsto in Fase 2.
    """
    _ = (actions, model, kwargs)
    if not available():
        require("socceraction")
    raise NotImplementedError("metrics.socceraction.vaep: previsto in Fase 2.")


def xt_from_actions(actions: pd.DataFrame, model: Any | None = None, **kwargs: Any) -> pd.Series:
    """Calcola l'xT a partire da azioni SPADL.

    Args:
        actions: Azioni SPADL.
        model: Modello da usare; se omesso, si carica quello predefinito.
        **kwargs: Argomenti aggiuntivi.

    Returns:
        Serie con il valore xT per azione.

    Raises:
        MissingDependencyError: Se ``socceraction`` non è installato.
        NotImplementedError: Previsto in Fase 2.
    """
    _ = (actions, model, kwargs)
    if not available():
        require("socceraction")
    raise NotImplementedError("metrics.socceraction.xt_from_actions: previsto in Fase 2.")
