"""Cache su disco per i risultati delle query.

Obiettivo: non riscaricare e non ricalcolare due volte la stessa cosa. La cache è
deliberatamente stupida e trasparente — una chiave è un hash dei parametri della
query, un valore è un DataFrame più un file di metadati — perché una cache "furba"
che indovina le chiavi è una cache che restituisce in silenzio il risultato sbagliato.

Garanzie:

* **chiave deterministica**: stessi parametri, stessa chiave, su qualsiasi macchina
  (i parametri sono serializzati in JSON con chiavi ordinate prima dell'hash);
* **scrittura atomica**: un file temporaneo viene rinominato sul file finale, quindi
  un'interruzione non lascia una voce a metà;
* **provenienza**: ogni voce registra i parametri originali e la data di scrittura,
  così si può capire da dove viene un dato vecchio;
* **nessuna dipendenza obbligatoria oltre a pandas**: Parquet se disponibile,
  altrimenti CSV, dichiarato nei metadati.

Example:
    >>> from openzone.warehouse import Cache
    >>> cache = Cache(namespace="understat")
    >>> key = cache.key("shots", league="Serie A", season="2024")
    >>> cache.has(key)
    False
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from openzone._deps import has

__all__ = ["Cache", "CacheEntry", "CacheStats", "default_root"]

#: Variabile d'ambiente che sovrascrive la directory radice della cache.
ROOT_ENV_VAR = "OPENZONE_CACHE_DIR"

#: Nome della directory predefinita, creata nella directory di lavoro.
DEFAULT_DIRNAME = ".openzone_cache"

#: Versione del formato delle voci: va incrementata quando cambia la struttura su disco.
FORMAT_VERSION = 1


def default_root() -> Path:
    """Determina la directory radice della cache.

    Returns:
        Il valore di ``OPENZONE_CACHE_DIR`` se impostato, altrimenti
        ``./.openzone_cache`` rispetto alla directory di lavoro corrente.
    """
    override = os.environ.get(ROOT_ENV_VAR, "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (Path.cwd() / DEFAULT_DIRNAME).resolve()


@dataclass(frozen=True)
class CacheEntry:
    """Voce di cache presente su disco.

    Attributes:
        key: Chiave esadecimale della voce.
        namespace: Namespace di appartenenza.
        path: Percorso del file dati.
        meta_path: Percorso del file di metadati.
        created_at: Istante di scrittura, in secondi epoch.
        format: ``"parquet"`` o ``"csv"``.
        params: Parametri originali della query.
        rows: Numero di righe salvate.
    """

    key: str
    namespace: str
    path: Path
    meta_path: Path
    created_at: float
    format: str
    params: dict[str, Any]
    rows: int

    @property
    def age_seconds(self) -> float:
        """Età della voce in secondi."""
        return max(0.0, time.time() - self.created_at)

    @property
    def size_bytes(self) -> int:
        """Dimensione su disco del file dati, in byte."""
        return self.path.stat().st_size if self.path.is_file() else 0


@dataclass(frozen=True)
class CacheStats:
    """Riepilogo del contenuto di un namespace.

    Attributes:
        namespace: Namespace riepilogato.
        entries: Numero di voci presenti.
        bytes_on_disk: Somma delle dimensioni dei file dati.
        oldest: Data della voce più vecchia, o ``None`` se vuoto.
        newest: Data della voce più recente, o ``None`` se vuoto.
    """

    namespace: str
    entries: int
    bytes_on_disk: int
    oldest: float | None
    newest: float | None


class Cache:
    """Cache su disco di DataFrame, indicizzata da una chiave deterministica.

    Args:
        root: Directory radice. Se omessa, si usa :func:`default_root`.
        namespace: Sottodirectory logica, tipicamente il nome della fonte o della
            fase di calcolo. Tenerli separati evita collisioni fra dati grezzi e
            dati derivati.

    Example:
        >>> cache = Cache(namespace="eventi")
        >>> key = cache.key("events", match_id=42)
        >>> _ = cache.put(key, pd.DataFrame({"a": [1]}))  # doctest: +SKIP
        >>> cache.get(key) is not None  # doctest: +SKIP
        True
    """

    def __init__(self, root: str | Path | None = None, namespace: str = "default") -> None:
        """Prepara la cache e crea la directory del namespace.

        Args:
            root: Directory radice. Se omessa, si usa :func:`default_root`.
            namespace: Sottodirectory logica del namespace.
        """
        self.root = Path(root).expanduser().resolve() if root is not None else default_root()
        self.namespace = namespace
        self.directory = self.root / namespace
        self.directory.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ chiavi

    @staticmethod
    def key(*parts: Any, **params: Any) -> str:
        """Calcola una chiave deterministica dai parametri della query.

        La serializzazione è JSON con chiavi ordinate e rappresentazione stabile
        dei valori, quindi la stessa query produce la stessa chiave su macchine
        diverse.

        Args:
            *parts: Valori posizionali che identificano la query.
            **params: Parametri con nome che identificano la query.

        Returns:
            Chiave esadecimale di 64 caratteri.

        Raises:
            TypeError: Se un parametro non è serializzabile in JSON.
        """
        payload = {"parts": list(parts), "params": params}
        try:
            encoded = json.dumps(payload, sort_keys=True, default=repr, ensure_ascii=False)
        except TypeError as exc:  # pragma: no cover - default=repr copre quasi tutto
            raise TypeError(f"Parametri non serializzabili per la chiave di cache: {exc}") from exc
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------- percorsi

    def _paths(self, key: str) -> tuple[Path, Path]:
        """Restituisce i percorsi del file dati e dei metadati di una chiave.

        Args:
            key: Chiave esadecimale.

        Returns:
            Coppia ``(percorso_dati, percorso_metadati)``.

        Raises:
            ValueError: Se la chiave non ha la forma attesa.
        """
        if len(key) != 64 or not all(char in "0123456789abcdef" for char in key):
            raise ValueError(
                f"Chiave di cache non valida: {key!r}. Usa Cache.key(...) per generarla."
            )
        return self.directory / f"{key}.data", self.directory / f"{key}.json"

    def _entry_for(self, key: str) -> CacheEntry:
        """Costruisce la voce corrispondente a una chiave presente su disco.

        Args:
            key: Chiave esadecimale.

        Returns:
            La voce di cache.

        Raises:
            FileNotFoundError: Se i file della voce non esistono.
        """
        data_path, meta_path = self._paths(key)
        if not data_path.is_file() or not meta_path.is_file():
            raise FileNotFoundError(f"Voce di cache assente: {key}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return CacheEntry(
            key=key,
            namespace=self.namespace,
            path=data_path,
            meta_path=meta_path,
            created_at=float(meta.get("created_at", 0.0)),
            format=str(meta.get("format", "csv")),
            params=dict(meta.get("params", {})),
            rows=int(meta.get("rows", 0)),
        )

    # ------------------------------------------------------------ operazioni

    def has(self, key: str) -> bool:
        """Verifica se una voce è presente e leggibile.

        Args:
            key: Chiave esadecimale.

        Returns:
            ``True`` se dati e metadati esistono.
        """
        data_path, meta_path = self._paths(key)
        return data_path.is_file() and meta_path.is_file()

    def get(self, key: str) -> pd.DataFrame | None:
        """Legge una voce di cache.

        Args:
            key: Chiave esadecimale.

        Returns:
            Il DataFrame salvato, oppure ``None`` se la voce è assente. Gli attributi
            ``attrs`` riportano chiave, namespace, formato e data di scrittura.

        Raises:
            ValueError: Se la chiave non ha la forma attesa.
        """
        if not self.has(key):
            return None
        entry = self._entry_for(key)
        if entry.format == "parquet" and has("pyarrow"):
            frame = pd.read_parquet(entry.path)
        else:
            frame = pd.read_csv(entry.path)
        frame.attrs["openzone.cache_key"] = entry.key
        frame.attrs["openzone.cache_namespace"] = entry.namespace
        frame.attrs["openzone.cache_created_at"] = entry.created_at
        return frame

    def put(self, key: str, frame: pd.DataFrame, **params: Any) -> CacheEntry:
        """Salva un DataFrame in cache.

        La scrittura è atomica: il file viene creato con un nome temporaneo nella
        stessa directory e poi rinominato, così un'interruzione non lascia una voce
        corrotta.

        Args:
            key: Chiave esadecimale, da :meth:`key`.
            frame: DataFrame da salvare.
            **params: Parametri originali della query, registrati nei metadati.

        Returns:
            La voce scritta.

        Raises:
            TypeError: Se ``frame`` non è un DataFrame.
            ValueError: Se la chiave non ha la forma attesa.
        """
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"La cache salva solo DataFrame, ricevuto: {type(frame).__name__}")
        data_path, meta_path = self._paths(key)
        use_parquet = has("pyarrow")
        fmt = "parquet" if use_parquet else "csv"

        tmp_data = data_path.with_suffix(".data.tmp")
        if use_parquet:
            frame.to_parquet(tmp_data, index=False)
        else:
            frame.to_csv(tmp_data, index=False)
        os.replace(tmp_data, data_path)

        meta = {
            "format_version": FORMAT_VERSION,
            "format": fmt,
            "namespace": self.namespace,
            "created_at": time.time(),
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "params": params,
        }
        tmp_meta = meta_path.with_suffix(".json.tmp")
        tmp_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp_meta, meta_path)

        return self._entry_for(key)

    def delete(self, key: str) -> bool:
        """Rimuove una voce di cache.

        Args:
            key: Chiave esadecimale.

        Returns:
            ``True`` se la voce esisteva ed è stata rimossa.
        """
        existed = self.has(key)
        for path in self._paths(key):
            path.unlink(missing_ok=True)
        return existed

    def entries(self) -> list[CacheEntry]:
        """Elenca le voci presenti nel namespace.

        Returns:
            Le voci, dalla più recente alla più vecchia. I file incompleti (dati
            senza metadati o viceversa) vengono ignorati.
        """
        found: list[CacheEntry] = []
        for meta_path in self.directory.glob("*.json"):
            key = meta_path.stem
            if self.has(key):
                found.append(self._entry_for(key))
        return sorted(found, key=lambda item: item.created_at, reverse=True)

    def stats(self) -> CacheStats:
        """Riepiloga il contenuto del namespace.

        Returns:
            Conteggio, dimensione su disco ed estremi temporali delle voci.
        """
        items = self.entries()
        if not items:
            return CacheStats(self.namespace, 0, 0, None, None)
        times = [item.created_at for item in items]
        return CacheStats(
            namespace=self.namespace,
            entries=len(items),
            bytes_on_disk=sum(item.size_bytes for item in items),
            oldest=min(times),
            newest=max(times),
        )

    def evict(self, older_than_seconds: float) -> int:
        """Rimuove le voci più vecchie di una soglia.

        Args:
            older_than_seconds: Età minima, in secondi, perché una voce sia rimossa.

        Returns:
            Numero di voci rimosse.

        Raises:
            ValueError: Se la soglia è negativa.
        """
        if older_than_seconds < 0:
            raise ValueError("older_than_seconds non può essere negativo")
        removed = 0
        for item in self.entries():
            if item.age_seconds > older_than_seconds:
                self.delete(item.key)
                removed += 1
        return removed

    def clear(self) -> None:
        """Svuota completamente il namespace."""
        shutil.rmtree(self.directory, ignore_errors=True)
        self.directory.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        """Rappresentazione leggibile, con namespace e directory."""
        return f"Cache(namespace={self.namespace!r}, directory={str(self.directory)!r})"
