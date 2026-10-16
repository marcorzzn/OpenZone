# `openzone.metrics`

Metriche calcistiche, divise per **generazione**: non per difficoltà di calcolo, ma per
quanto il numero dipende da un modello.

| Modulo | Generazione | Stato |
|---|---|---|
| [`basic.py`](basic.py) | 1ª — conteggi dagli eventi | **implementato e testato** (tranne assist e key passes) |
| [`advanced.py`](advanced.py) | 2ª — qualità del singolo evento | `source_xg` implementato; modelli in Fase 2 |
| [`predictive.py`](predictive.py) | 3ª — valore, pressing, progressione | progressione e PPDA implementati; xT e packing in Fase 2-3 |
| [`socceraction.py`](socceraction.py) | 3ª — VAEP e xT su azioni SPADL | wrapper pronto, modelli in Fase 2 |

## La regola del modulo

**Una metrica che non è calcolabile con i dati disponibili solleva un errore esplicito.**
Non restituisce mai un'approssimazione silenziosa: un numero sbagliato con l'aspetto di un
numero giusto è il danno peggiore che una libreria di analisi possa fare.

Esempi concreti di questa regola:

* `compute_xgot` fallisce se mancano le coordinate post-shot, perché Understat e
  StatsBomb Open Data non le espongono;
* `basic.assists` e `basic.key_passes` falliscono finché non è definita la ricostruzione
  delle sequenze di possesso;
* `compute_ppda` restituisce `None` quando non ci sono azioni difensive, invece di zero o
  infinito.

## Separazione fra xG della fonte e xG di OpenZone

`advanced.source_xg` legge l'xG che la fonte fornisce insieme all'evento; `compute_xg`
calcola l'xG con un modello proprio. Sono due cose diverse: nel DataFrame finiscono in
colonne diverse, con nomi diversi. Sommarli o sovrascriverne uno con l'altro è l'errore
che questa separazione esiste per impedire.

## Parametri sempre dichiarati

Le metriche sensibili ai parametri li espongono come argomenti e li restituiscono nel
risultato: la soglia dei passaggi progressivi, la zona di pressing del PPDA e le famiglie
contate come azione difensiva. Un PPDA o un conteggio di passaggi progressivi senza i
propri parametri non è confrontabile con niente.

## Esempio

```python
from openzone.metrics import basic, predictive

shots = basic.shots(events)
predictive.progressive_passes(events, threshold_m=10.0)
result = predictive.compute_ppda(events, team_id=1, pressing_height=0.4)
result.as_row()   # include i parametri usati
```
