"""Metriche di 3ª generazione: valore delle azioni, pressing, progressione.

Sono le metriche che dipendono dal contesto: la stessa azione vale cose diverse a
seconda di dove avviene, di chi la subisce e di cosa succede dopo. Qui la sensibilità
ai parametri è alta, quindi ogni funzione espone i propri parametri come argomenti
espliciti e li restituisce insieme al risultato.

Implementato in questo modulo:

* conversione delle coordinate in metri, necessaria a qualunque soglia espressa in
  metri;
* avanzamento verso la porta;
* passaggi progressivi e conduzioni progressive, con soglia parametrica;
* PPDA, con zona di pressing e azioni difensive dichiarate.

Non implementato, con motivazione:

* xT — richiede l'addestramento della matrice di transizione (Fase 2-3);
* packing — richiede le posizioni di tutti i giocatori, quindi tracking data.

Example:
    >>> from openzone.metrics import predictive
    >>> predictive.progression_metres(50.0, 80.0)  # doctest: +SKIP
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

import pandas as pd

from openzone.exceptions import OpenZoneError

__all__ = [
    "DEFENSIVE_ACTIONS",
    "DEFAULT_PITCH_LENGTH_M",
    "DEFAULT_PITCH_WIDTH_M",
    "DEFAULT_PRESSING_HEIGHT",
    "DEFAULT_PROGRESSION_THRESHOLD_M",
    "PPDAResult",
    "compute_ppda",
    "compute_xt",
    "packing",
    "progressive_carries",
    "progressive_passes",
    "progression_metres",
    "to_metres",
]

#: Lunghezza del campo in metri, usata per convertire le coordinate normalizzate.
DEFAULT_PITCH_LENGTH_M: Final[float] = 105.0

#: Larghezza del campo in metri.
DEFAULT_PITCH_WIDTH_M: Final[float] = 68.0

#: Soglia predefinita di avanzamento per un passaggio progressivo, in metri.
DEFAULT_PROGRESSION_THRESHOLD_M: Final[float] = 10.0

#: Altezza predefinita della zona di pressing: quota di campo, misurata dall'area
#: avversaria verso la propria porta. 0.40 significa "il 40% del campo più avanzato".
DEFAULT_PRESSING_HEIGHT: Final[float] = 0.40

#: Famiglie di eventi che contano come azione difensiva nel PPDA.
DEFENSIVE_ACTIONS: Final[tuple[str, ...]] = ("defensive", "duel", "foul")


@dataclass(frozen=True)
class PPDAResult:
    """Risultato del PPDA con i parametri usati.

    Attributes:
        value: Il rapporto passaggi concessi / azioni difensive, oppure ``None`` se il
            denominatore è zero.
        opponent_passes: Passaggi avversari nella zona di pressing.
        defensive_actions: Azioni difensive nella zona di pressing.
        pressing_height: Quota di campo usata come zona di pressing.
        action_families: Famiglie contate come azione difensiva.
    """

    value: float | None
    opponent_passes: int
    defensive_actions: int
    pressing_height: float
    action_families: tuple[str, ...]

    def as_row(self) -> dict[str, Any]:
        """Converte il risultato in una riga piatta.

        Returns:
            Dizionario con i valori e i parametri, pronto per un DataFrame.
        """
        return {
            "ppda": self.value,
            "opponent_passes": self.opponent_passes,
            "defensive_actions": self.defensive_actions,
            "pressing_height": self.pressing_height,
            "action_families": ",".join(self.action_families),
        }


def to_metres(
    x: pd.Series,
    y: pd.Series,
    *,
    length_m: float = DEFAULT_PITCH_LENGTH_M,
    width_m: float = DEFAULT_PITCH_WIDTH_M,
    pitch_size: float = 100.0,
) -> tuple[pd.Series, pd.Series]:
    """Converte coordinate normalizzate in metri.

    Args:
        x: Coordinata x normalizzata (0-100 nello schema canonico).
        y: Coordinata y normalizzata.
        length_m: Lunghezza reale del campo in metri.
        width_m: Larghezza reale del campo in metri.
        pitch_size: Estensione del sistema normalizzato (100 nello schema canonico).

    Returns:
        Coppia di Serie ``(x_metri, y_metri)``.
    """
    return (x / pitch_size * length_m, y / pitch_size * width_m)


def progression_metres(
    start_x_m: float,
    end_x_m: float,
    *,
    length_m: float = DEFAULT_PITCH_LENGTH_M,
) -> float:
    """Calcola l'avanzamento verso la porta avversaria, in metri.

    Args:
        start_x_m: Coordinata x di partenza, in metri.
        end_x_m: Coordinata x di arrivo, in metri.
        length_m: Lunghezza del campo in metri.

    Returns:
        Avanzamento in metri: positivo se il pallone si è mosso verso la porta
        avversaria, negativo se all'indietro.

    Example:
        >>> progression_metres(30.0, 45.0)
        15.0
        >>> progression_metres(45.0, 30.0)
        -15.0
    """
    _ = length_m
    return end_x_m - start_x_m


def _progression_mask(
    events: pd.DataFrame,
    family: str,
    threshold_m: float,
    length_m: float,
    pitch_size: float,
) -> pd.Series:
    """Costruisce la maschera degli eventi che superano la soglia di avanzamento.

    Args:
        events: Eventi standardizzati.
        family: Famiglia da filtrare.
        threshold_m: Soglia di avanzamento in metri.
        length_m: Lunghezza del campo in metri.
        pitch_size: Estensione del sistema normalizzato.

    Returns:
        Serie booleana allineata a ``events``.

    Raises:
        OpenZoneError: Se mancano le colonne necessarie.
    """
    required = ("family", "x", "end_x")
    missing = [column for column in required if column not in events.columns]
    if missing:
        raise OpenZoneError(
            f"Metriche di progressione: colonne mancanti {', '.join(missing)}. "
            "Servono le coordinate di partenza e di arrivo di ogni azione."
        )
    factor = length_m / pitch_size
    start = events["x"].astype("float64") * factor
    end = events["end_x"].astype("float64") * factor
    return (events["family"] == family) & ((end - start) >= threshold_m)


def progressive_passes(
    events: pd.DataFrame,
    threshold_m: float = DEFAULT_PROGRESSION_THRESHOLD_M,
    *,
    completed_only: bool = True,
    length_m: float = DEFAULT_PITCH_LENGTH_M,
    pitch_size: float = 100.0,
) -> pd.DataFrame:
    """Restituisce i passaggi progressivi.

    La soglia è un argomento, non una costante nascosta, perché non è universale: Opta
    usa 10 m con criteri aggiuntivi, altre fonti 5 m o una frazione di campo. Il valore
    usato va citato insieme al risultato.

    Args:
        events: Eventi standardizzati.
        threshold_m: Soglia di avanzamento in metri.
        completed_only: Considera solo i passaggi riusciti. È il comportamento
            predefinito delle metriche pubbliche.
        length_m: Lunghezza del campo in metri.
        pitch_size: Estensione del sistema normalizzato.

    Returns:
        Le righe di passaggio progressivo, con la colonna ``progression_m`` aggiunta.
    """
    mask = _progression_mask(events, "pass", threshold_m, length_m, pitch_size)
    if completed_only and "outcome" in events.columns:
        mask &= events["outcome"].astype("boolean").fillna(False)
    selected = events.loc[mask].copy()
    factor = length_m / pitch_size
    selected["progression_m"] = (
        selected["end_x"].astype("float64") - selected["x"].astype("float64")
    ) * factor
    selected["threshold_m"] = threshold_m
    return selected


def progressive_carries(
    events: pd.DataFrame,
    threshold_m: float = DEFAULT_PROGRESSION_THRESHOLD_M,
    *,
    length_m: float = DEFAULT_PITCH_LENGTH_M,
    pitch_size: float = 100.0,
) -> pd.DataFrame:
    """Restituisce le conduzioni progressive.

    Richiede che la fonte registri le conduzioni come eventi con coordinate di partenza
    e di arrivo: StatsBomb lo fa, molte fonti evento no.

    Args:
        events: Eventi standardizzati.
        threshold_m: Soglia di avanzamento in metri.
        length_m: Lunghezza del campo in metri.
        pitch_size: Estensione del sistema normalizzato.

    Returns:
        Le righe di conduzione progressiva, con la colonna ``progression_m`` aggiunta.
    """
    mask = _progression_mask(events, "carry", threshold_m, length_m, pitch_size)
    selected = events.loc[mask].copy()
    factor = length_m / pitch_size
    selected["progression_m"] = (
        selected["end_x"].astype("float64") - selected["x"].astype("float64")
    ) * factor
    selected["threshold_m"] = threshold_m
    return selected


def compute_ppda(
    events: pd.DataFrame,
    team_id: Any,
    *,
    pressing_height: float = DEFAULT_PRESSING_HEIGHT,
    action_families: tuple[str, ...] = DEFENSIVE_ACTIONS,
    pitch_size: float = 100.0,
) -> PPDAResult:
    """Calcola il PPDA di una squadra, con parametri dichiarati.

    Il PPDA è un rapporto: passaggi concessi agli avversari diviso azioni difensive
    fatte, entrambi limitati a una zona di pressing. Il valore assoluto cambia molto al
    variare di due parametri — l'estensione della zona e quali eventi contano come
    azione difensiva — quindi entrambi sono argomenti e vengono restituiti nel
    risultato.

    Args:
        events: Eventi standardizzati di una partita (o di più partite, se si vuole un
            valore aggregato).
        team_id: Squadra di cui calcolare il PPDA: i passaggi contati sono quelli degli
            avversari, le azioni difensive quelle di questa squadra.
        pressing_height: Quota di campo, dal fondo verso la porta avversaria, che
            definisce la zona di pressing.
        action_families: Famiglie contate come azione difensiva.
        pitch_size: Estensione del sistema normalizzato.

    Returns:
        Il risultato con valore e parametri usati.

    Raises:
        OpenZoneError: Se mancano le colonne necessarie o la zona non è valida.
        ValueError: Se ``pressing_height`` non è compreso fra 0 e 1.

    Example:
        >>> result = compute_ppda(events, team_id=1)  # doctest: +SKIP
        >>> result.value  # doctest: +SKIP
        8.4
    """
    if not 0 < pressing_height <= 1:
        raise ValueError(f"pressing_height deve essere in (0, 1], ricevuto: {pressing_height}")
    required = ("team_id", "family", "x")
    missing = [column for column in required if column not in events.columns]
    if missing:
        raise OpenZoneError(
            f"PPDA: colonne mancanti {', '.join(missing)}. "
            "Servono la squadra, la famiglia dell'evento e la coordinata x."
        )

    threshold = pitch_size * (1.0 - pressing_height)
    in_zone = events["x"].astype("float64") >= threshold

    opponent_passes = int(
        (in_zone & (events["family"] == "pass") & (events["team_id"] != team_id)).sum()
    )
    defensive_actions = int(
        (in_zone & (events["team_id"] == team_id) & (events["family"].isin(action_families))).sum()
    )

    value = (
        opponent_passes / defensive_actions if defensive_actions > 0 else None
    )
    return PPDAResult(
        value=value,
        opponent_passes=opponent_passes,
        defensive_actions=defensive_actions,
        pressing_height=pressing_height,
        action_families=tuple(action_families),
    )


def compute_xt(events: pd.DataFrame, **kwargs: Any) -> pd.Series:
    """Calcola l'Expected Threat per ogni evento.

    Args:
        events: Eventi standardizzati.
        **kwargs: Parametri del modello (griglia, dataset di addestramento).

    Returns:
        Serie con il valore xT associato a ogni evento.

    Raises:
        NotImplementedError: Richiede l'addestramento della matrice di transizione sulla
            griglia scelta. Previsto in Fase 2-3: un xT con coefficienti arbitrari
            sarebbe peggio di nessun xT.
    """
    _ = (events, kwargs)
    raise NotImplementedError(
        "predictive.compute_xt: la matrice di transizione va addestrata e validata "
        "(vedi openzone.glossary.get_glossary('xt')). Previsto in Fase 2-3."
    )


def packing(events: pd.DataFrame, positions: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
    """Conta gli avversari superati da ogni azione.

    Args:
        events: Eventi standardizzati.
        positions: Posizioni dei giocatori al momento di ciascuna azione, con le colonne
            ``event_id``, ``player_id``, ``team_id``, ``x`` e ``y``.
        **kwargs: Parametri aggiuntivi.

    Returns:
        Gli eventi con la colonna ``packing``, cioè il numero di avversari superati.

    Raises:
        OpenZoneError: Se la tabella delle posizioni è vuota.
        NotImplementedError: Il calcolo è previsto in Fase 3.
    """
    if positions is None or len(positions) == 0:
        raise OpenZoneError(
            "packing richiede le posizioni di tutti i giocatori al momento dell'azione. "
            "Con i soli dati evento non è calcolabile."
        )
    _ = (events, kwargs)
    raise NotImplementedError("predictive.packing: previsto in Fase 3.")
