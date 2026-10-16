"""Storage locale: warehouse colonnare e cache su disco.

Due strumenti con scopi diversi e complementari:

* :class:`~openzone.warehouse.cache.Cache` evita di ripetere un download o un calcolo
  già fatto, con chiavi deterministiche e scritture atomiche;
* :class:`~openzone.warehouse.duckdb.Warehouse` interroga Parquet e DataFrame senza
  caricarli interamente in memoria, ed è il modo previsto per lavorare su più stagioni.

Entrambi usano dipendenze opzionali: la cache funziona con il solo ``pandas`` (Parquet
se ``pyarrow`` è presente, altrimenti CSV), il warehouse richiede ``duckdb``.

Example:
    >>> from openzone.warehouse import Cache, default_root
    >>> Cache(namespace="prova").directory.name
    'prova'
"""

from __future__ import annotations

from openzone.warehouse.cache import Cache, CacheEntry, CacheStats, default_root

__all__ = ["Cache", "CacheEntry", "CacheStats", "Warehouse", "default_root"]


def __getattr__(name: str) -> object:
    """Espone ``Warehouse`` senza importare ``duckdb`` finché non serve.

    Args:
        name: Attributo richiesto sul modulo.

    Returns:
        La classe richiesta.

    Raises:
        AttributeError: Se il nome non fa parte della superficie del modulo.
    """
    if name == "Warehouse":
        from openzone.warehouse.duckdb import Warehouse

        return Warehouse
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Elenca gli attributi del modulo, inclusi quelli pigri."""
    return sorted({*globals(), "Warehouse"})
