# `openzone.warehouse`

Storage locale: due strumenti con scopi diversi.

| Modulo | Ruolo | Dipendenze | Stato |
|---|---|---|---|
| [`cache.py`](cache.py) | Cache su disco con chiave deterministica | `pandas` (Parquet se `pyarrow`) | **implementato e testato** |
| [`duckdb.py`](duckdb.py) | Warehouse colonnare per Parquet e DataFrame | `duckdb` | implementato |

## Cache

Una chiave è l'hash SHA-256 dei parametri della query, serializzati in JSON con chiavi
ordinate: stessi parametri, stessa chiave, su qualsiasi macchina. Le scritture sono
atomiche (file temporaneo e rename), quindi un'interruzione non lascia voci corrotte, e
ogni voce registra i parametri originali per poter risalire alla query.

```python
from openzone.warehouse import Cache

cache = Cache(namespace="understat")
key = cache.key("shots", league="Serie A", season="2024")

frame = cache.get(key)
if frame is None:
    frame = scarica_e_calcola()
    cache.put(key, frame, league="Serie A", season="2024")

cache.stats()          # conteggio, byte su disco, voci più vecchie e più recenti
cache.evict(30 * 86400)  # rimuove le voci più vecchie di 30 giorni
```

La directory radice predefinita è `./.openzone_cache`, sovrascrivibile con la variabile
d'ambiente `OPENZONE_CACHE_DIR`.

## Warehouse

```python
from openzone.warehouse import Warehouse

with Warehouse("data/openzone.duckdb") as wh:
    wh.register_parquet("events", "data/events/*.parquet")
    shots = wh.query("SELECT * FROM events WHERE family = 'shot'")
    wh.count("events")
```

Il file del database è un artefatto locale e non va versionato: è già in `.gitignore`.
Due processi non devono scrivere lo stesso file contemporaneamente.
