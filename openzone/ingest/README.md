# `openzone.ingest`

Acquisizione dati dalle fonti esterne. Ogni sottomodulo incapsula una fonte e le sue
dipendenze: se una fonte cambia formato o si rompe, si aggiusta un file.

## Adapter

| Sottomodulo | Fonte | Dipendenze | Stato |
|---|---|---|---|
| [`statsbomb.py`](statsbomb.py) | StatsBomb Open Data | solo `pandas` | **usabile** |
| [`datahub.py`](datahub.py) | CSV/Parquet a livello partita | solo `pandas` | **usabile** |
| [`pannadata.py`](pannadata.py) | Opta Parquet locali | `pyarrow` | usabile con extra `ingest` |
| [`soccerdata.py`](soccerdata.py) | FBref, FotMob, Sofascore, ... | `soccerdata` | wrapper pronto |
| [`understat.py`](understat.py) | Understat | `soccerdata` | wrapper pronto |
| [`whoscored.py`](whoscored.py) | WhoScored | `soccerdata` | wrapper pronto, ToS vietano lo scraping |
| [`scraperfc.py`](scraperfc.py) | Varie (fallback) | `ScraperFC` | wrapper pronto |
| [`football_data_org.py`](football_data_org.py) | football-data.org | `requests` + chiave API | usabile con chiave |

## Contratto

Gli adapter restituiscono dati **grezzi**, con i nomi di colonna della fonte, e non
normalizzano: la normalizzazione è responsabilità di [`openzone.standardize`](../standardize).
Un adapter che "aggiusta" i dati a metà strada rende impossibile capire da dove viene un
numero. Il contratto è descritto in [`_base.py`](_base.py).

## Licenze

Prima di usare una fonte, leggi la sua scheda in
[`glossary/sources.yaml`](../glossary/sources.yaml). In sintesi: nessun adapter scarica
dati che la fonte vieti di ridistribuire, `pannadata` legge solo file locali e
`whoscored`/`sofascore` non vanno usati in produzione.

## Esempio

```python
from openzone.ingest import statsbomb

matches = statsbomb.load_matches()          # Serie A 2015/16
events = statsbomb.load_events(matches.loc[0, "match_id"])
lineups = statsbomb.load_lineups(matches.loc[0, "match_id"])
```
