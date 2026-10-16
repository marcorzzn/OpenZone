"""Warehouse colonnare su DuckDB.

DuckDB legge Parquet e DataFrame direttamente, senza caricare tutto in memoria, ed è
il modo più economico per fare query su più stagioni di eventi. Qui è incapsulato in
una classe piccola: connessione pigra, registrazione di tabelle e viste, query che
restituisce DataFrame.

Il file del database è un artefatto locale, non versionato (vedi ``.gitignore``).
Ogni connessione a un file reale è serializzata da DuckDB stesso: due processi che
scrivono lo stesso file non sono supportati.

Example:
    >>> from openzone.warehouse import Warehouse
    >>> with Warehouse(":memory:") as wh:  # doctest: +SKIP
    ...     wh.register("events", events_frame)
    ...     shots = wh.query("SELECT * FROM events WHERE type_name = 'Shot'")
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from openzone._deps import require

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd

__all__ = ["Warehouse", "read_parquet"]

#: Nome della vista con cui si interrogano i file Parquet registrati.
DEFAULT_PARQUET_VIEW = "parquet_scan"


class Warehouse:
    """Wrapper minimale su una connessione DuckDB.

    Args:
        path: Percorso del file di database, oppure ``":memory:"`` per un database
            temporaneo in memoria. La directory padre viene creata se manca.
        read_only: Apre il database in sola lettura. Utile per condividere un
            warehouse già costruito senza rischiare scritture accidentali.

    Raises:
        MissingDependencyError: Se ``duckdb`` non è installato.
    """

    def __init__(self, path: str | Path = ":memory:", *, read_only: bool = False) -> None:
        """Verifica la dipendenza, prepara la directory e rimanda la connessione.

        Args:
            path: Percorso del file di database, oppure ``":memory:"``.
            read_only: Apre il database in sola lettura.

        Raises:
            MissingDependencyError: Se ``duckdb`` non è installato.
        """
        self._duckdb = require("duckdb")
        self.path = str(path)
        self.read_only = read_only
        if self.path != ":memory:":
            parent = Path(self.path).expanduser().resolve().parent
            parent.mkdir(parents=True, exist_ok=True)
        self._connection: Any | None = None

    # ----------------------------------------------------------- connessione

    @property
    def connection(self) -> Any:
        """Connessione DuckDB, aperta alla prima richiesta."""
        if self._connection is None:
            self._connection = self._duckdb.connect(self.path, read_only=self.read_only)
        return self._connection

    def close(self) -> None:
        """Chiude la connessione, se aperta. Idempotente."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> Warehouse:
        """Entra nel contesto: la connessione si apre alla prima query."""
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Esce dal contesto chiudendo la connessione."""
        self.close()

    # ------------------------------------------------------------ operazioni

    def execute(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> Any:
        """Esegue un'istruzione SQL che non restituisce righe.

        Args:
            sql: Istruzione SQL.
            params: Parametri posizionali, passati come segnaposto ``?``.

        Returns:
            L'oggetto risultato di DuckDB.
        """
        return self.connection.execute(sql, params) if params else self.connection.execute(sql)

    def query(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> pd.DataFrame:
        """Esegue una query e restituisce un DataFrame.

        Args:
            sql: Query SQL.
            params: Parametri posizionali, passati come segnaposto ``?``.

        Returns:
            Il risultato come DataFrame pandas.
        """
        result = self.execute(sql, params)
        frame = result.df()
        frame.attrs["openzone.warehouse"] = self.path
        frame.attrs["openzone.sql"] = " ".join(sql.split())
        return frame

    def register(self, name: str, frame: pd.DataFrame, *, replace: bool = True) -> None:
        """Registra un DataFrame come tabella interrogabile.

        La tabella è una vista sul DataFrame in memoria: le modifiche successive al
        DataFrame non si riflettono nella vista, perché DuckDB ne materializza i dati
        al momento della registrazione.

        Args:
            name: Nome della tabella.
            frame: DataFrame da registrare.
            replace: Sostituisce la tabella se esiste già.

        Raises:
            ValueError: Se il nome contiene caratteri non ammessi in SQL.
        """
        self._check_name(name)
        if replace:
            self.execute(f'DROP TABLE IF EXISTS "{name}"')
        self.connection.register(name, frame)

    def register_parquet(
        self,
        view_name: str,
        path_or_glob: str | Path,
        *,
        replace: bool = True,
        hive_partitioning: bool = False,
    ) -> None:
        """Crea una vista su uno o più file Parquet.

        È il modo consigliato di lavorare su più stagioni: DuckDB legge solo le
        colonne e le partizioni richieste dalla query.

        Args:
            view_name: Nome della vista.
            path_or_glob: Percorso di un file o pattern glob (per esempio
                ``"data/events/*.parquet"``).
            replace: Sostituisce la vista se esiste già.
            hive_partitioning: Legge la struttura di directory come partizioni.

        Raises:
            ValueError: Se il nome della vista non è ammesso.
            FileNotFoundError: Se un percorso esplicito non esiste.
        """
        self._check_name(view_name)
        target = str(path_or_glob)
        has_glob = any(char in target for char in "*?[")
        if not has_glob:
            resolved = Path(target).expanduser().resolve()
            if not resolved.exists():
                raise FileNotFoundError(f"Percorso Parquet inesistente: {resolved}")
            target = str(resolved)
        if replace:
            self.execute(f'DROP VIEW IF EXISTS "{view_name}"')
        literal = target.replace("'", "''")
        self.execute(
            f'CREATE VIEW "{view_name}" AS SELECT * FROM '
            f"read_parquet('{literal}', hive_partitioning = "
            f"{str(bool(hive_partitioning)).lower()})"
        )

    def tables(self) -> pd.DataFrame:
        """Elenca tabelle e viste presenti nel database.

        Returns:
            DataFrame con nome, tipo e schema di ogni relazione.
        """
        return self.query(
            "SELECT table_name, table_type FROM information_schema.tables "
            "ORDER BY table_name"
        )

    def describe(self, name: str) -> pd.DataFrame:
        """Descrive le colonne di una tabella o vista.

        Args:
            name: Nome della relazione.

        Returns:
            DataFrame con nome, tipo e vincoli di ogni colonna.

        Raises:
            ValueError: Se il nome non è ammesso.
        """
        self._check_name(name)
        return self.query(f'DESCRIBE "{name}"')

    def count(self, name: str) -> int:
        """Conta le righe di una tabella o vista.

        Args:
            name: Nome della relazione.

        Returns:
            Numero di righe.

        Raises:
            ValueError: Se il nome non è ammesso.
        """
        self._check_name(name)
        frame = self.query(f'SELECT count(*) AS n FROM "{name}"')
        return int(frame["n"].iloc[0])

    @staticmethod
    def _check_name(name: str) -> None:
        """Verifica che un nome sia utilizzabile come identificatore SQL.

        Args:
            name: Nome da verificare.

        Raises:
            ValueError: Se il nome è vuoto o contiene caratteri non ammessi.
        """
        if not name or not all(char.isalnum() or char == "_" for char in name):
            raise ValueError(
                f"Nome non valido: {name!r}. Usa solo lettere, cifre e trattini bassi."
            )


def read_parquet(path_or_glob: str | Path, *, columns: list[str] | None = None) -> pd.DataFrame:
    """Legge uno o più file Parquet con DuckDB.

    Alternativa a :func:`pandas.read_parquet` quando non è installato un motore
    Parquet per pandas ma è disponibile DuckDB.

    Args:
        path_or_glob: Percorso di un file o pattern glob.
        columns: Colonne da leggere; se omesso, tutte.

    Returns:
        Il contenuto dei file come DataFrame.

    Raises:
        MissingDependencyError: Se ``duckdb`` non è installato.
    """
    require("duckdb")
    literal = str(path_or_glob).replace("'", "''")
    with Warehouse(":memory:") as warehouse:
        projection = "*" if not columns else ", ".join(f'"{column}"' for column in columns)
        return warehouse.query(f"SELECT {projection} FROM read_parquet('{literal}')")
