"""Eccezioni pubbliche di OpenZone.

Tutte le eccezioni sollevate deliberatamente dalla libreria derivano da
:class:`OpenZoneError`, così un'applicazione che la incorpora (per esempio
OpenPitch) può distinguere un errore di dominio da un bug inatteso.
"""

from __future__ import annotations

__all__ = [
    "MissingDependencyError",
    "MetricNotFoundError",
    "OpenZoneError",
    "SourceNotAvailableError",
]


class OpenZoneError(Exception):
    """Errore di dominio sollevato da OpenZone."""


class MissingDependencyError(OpenZoneError, ImportError):
    """Una dipendenza opzionale necessaria per l'operazione non è installata.

    Attributes:
        package: Nome del pacchetto Python mancante.
        extra: Nome dell'extra di ``pyproject.toml`` che lo installa.
    """

    def __init__(self, package: str, extra: str | None = None, *, hint: str | None = None) -> None:
        """Costruisce l'errore con il comando di installazione da eseguire.

        Args:
            package: Nome del pacchetto Python mancante.
            extra: Nome dell'extra di ``pyproject.toml`` che lo installa.
            hint: Comando di installazione esplicito, se diverso da quello dedotto.
        """
        self.package = package
        self.extra = extra
        command = hint or (
            f'pip install "openzone[{extra}]"' if extra else f"pip install {package}"
        )
        message = f"Dipendenza opzionale mancante: {package!r}. Installala con: {command}"
        super().__init__(message)


class SourceNotAvailableError(OpenZoneError):
    """Una fonte dati non è raggiungibile o non è utilizzabile.

    Sollevata per esempio quando un adapter richiede credenziali assenti, quando la
    fonte risponde con un errore, o quando i suoi termini di servizio ne vietano
    l'uso programmatico.
    """


class MetricNotFoundError(OpenZoneError, KeyError):
    """La metrica richiesta non esiste nel glossario.

    Attributes:
        metric: Nome richiesto dall'utente.
        suggestions: Nomi noti sufficientemente simili, se presenti.
    """

    def __init__(self, metric: str, suggestions: list[str] | None = None) -> None:
        """Costruisce l'errore con i nomi simili fra cui scegliere.

        Args:
            metric: Nome richiesto dall'utente.
            suggestions: Nomi noti sufficientemente simili, se presenti.
        """
        self.metric = metric
        self.suggestions = list(suggestions or [])
        message = f"Metrica non trovata nel glossario: {metric!r}"
        if self.suggestions:
            message += f". Forse cercavi: {', '.join(self.suggestions)}"
        super().__init__(message)
