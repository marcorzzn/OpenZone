"""Disegno del campo.

Il campo è la base di ogni altro grafico. Qui vive la configurazione condivisa: tipo di
campo, dimensioni, colori, orientamento. Averla in un solo posto evita che due grafici
della stessa analisi mostrino campi leggermente diversi, che è il tipo di incoerenza che
fa dubitare di tutti i numeri.

Example:
    >>> from openzone.viz import pitch
    >>> pitch.available()
    False
"""

from __future__ import annotations

from typing import Any

__all__ = ["available", "draw_pitch", "pitch_dimensions"]

#: Dimensioni del campo in coordinate normalizzate.
NORMALISED_LENGTH = 100.0

#: Larghezza del campo in coordinate normalizzate.
NORMALISED_WIDTH = 100.0


def available() -> bool:
    """Indica se ``mplsoccer`` è installato.

    Returns:
        ``True`` se la libreria è importabile.
    """
    from openzone._deps import has

    return has("mplsoccer")


def pitch_dimensions(pitch_type: str = "opta") -> dict[str, float]:
    """Restituisce le dimensioni del campo per un tipo di ``mplsoccer``.

    Args:
        pitch_type: Tipo di campo (``"opta"``, ``"statsbomb"``, ``"wyscout"``).

    Returns:
        Dizionario con ``length`` e ``width`` nelle unità del tipo richiesto.
    """
    dimensions = {
        "opta": {"length": 100.0, "width": 100.0},
        "statsbomb": {"length": 120.0, "width": 80.0},
        "wyscout": {"length": 100.0, "width": 100.0},
    }
    if pitch_type not in dimensions:
        known = ", ".join(sorted(dimensions))
        raise KeyError(f"Tipo di campo non noto: {pitch_type!r}. Noti: {known}")
    return dict(dimensions[pitch_type])


def draw_pitch(pitch_type: str = "opta", **kwargs: Any) -> Any:
    """Crea una figura con il campo disegnato.

    Args:
        pitch_type: Tipo di campo.
        **kwargs: Argomenti passati a ``mplsoccer`` (colori, linee, orientamento).

    Returns:
        Coppia ``(figura, asse)``.

    Raises:
        MissingDependencyError: Se ``mplsoccer`` non è installato.
        NotImplementedError: Previsto in Fase 4.
    """
    from openzone._deps import require

    require("mplsoccer")
    _ = (pitch_type, kwargs)
    raise NotImplementedError("viz.pitch.draw_pitch: previsto in Fase 4.")
