# `openzone.spatial`

Analisi spaziale, ispirata a Soccermatics.

| Modulo | Ruolo | Dipendenze | Stato |
|---|---|---|---|
| [`half_spaces.py`](half_spaces.py) | Terzi, corridoi, half-spaces | `pandas` | **implementato e testato** |
| [`pressing_zones.py`](pressing_zones.py) | PPDA per fascia di campo | `pandas` | **implementato e testato** |
| [`pass_networks.py`](pass_networks.py) | Reti di passaggio | `pandas` + `networkx` per il grafo | archi implementati, grafo pronto |
| [`triangles.py`](triangles.py) | Triangoli di passaggio | `networkx` | implementato con l'extra `spatial` |
| [`pitch_control.py`](pitch_control.py) | Controllo del campo, TDA | tracking data | Fase 3 |

## Perché una reimplementazione e non `rpy2`

Soccermatics è un pacchetto R. Chiamarlo da Python via `rpy2` renderebbe OpenZone non
installabile con `pip` e non testabile in CI, per funzionalità che sono per lo più
geometria e teoria dei grafi. Il debito verso Soccermatics è culturale — i concetti e i
riferimenti — e va dichiarato nelle schede del glossario, non pagato con una dipendenza
da R.

## Prerequisito non negoziabile

Tutte le funzioni di questo modulo assumono che l'orientamento delle coordinate sia già
normalizzato fra i periodi (vedi
[`standardize.mapping.normalise_direction`](../standardize/mapping.py)). Applicarle a
coordinate grezze somma primo e secondo tempo come se fossero la stessa cosa.

## Il PPDA per fascia riusa la stessa definizione

`pressing_zones` non reimplementa il PPDA: chiama
[`metrics.predictive.compute_ppda`](../metrics/predictive.py) con la fascia come zona di
pressing. Una sola implementazione, un solo significato. Il conteggio degli eventi della
fascia è riportato accanto al valore, perché il PPDA di una fascia su una singola partita
è calcolato su poche decine di eventi ed è rumoroso.

## Esempio

```python
from openzone.spatial import half_spaces, pass_networks, pressing_zones

classified = half_spaces.classify(events)
half_spaces.zone_counts(classified)

edges = pass_networks.pass_edges(events, team_id=1)
pressing_zones.ppda_by_band(events, team_id=1)
```
