# `openzone.standardize`

Portare fonti diverse su un unico formato, senza perdere l'informazione su cosa manca.

| Modulo | Ruolo | Stato |
|---|---|---|
| [`schema.py`](schema.py) | Schema canonico: colonne, tipi, famiglie di eventi | **completo** |
| [`mapping.py`](mapping.py) | Coordinate, orientamenti, mappatura dei tipi evento | **completo** |
| [`kloppy.py`](kloppy.py) | Parsing dei formati via `kloppy` | wrapper pronto, conversione in Fase 1 |
| [`socceraction.py`](socceraction.py) | Conversione in azioni SPADL | wrapper pronto, conversione in Fase 2 |

## Lo schema canonico

Coordinate nel sistema Opta normalizzato 100x100, `x` verso la porta avversaria,
orientamento normalizzato fra i periodi, `qualifiers` sempre un dizionario. Le colonne e
i tipi sono in [`schema.py`](schema.py).

Due regole che valgono in tutto il package:

1. **un dato mancante resta mancante**: non diventa zero e non sparisce;
2. **un tipo evento non mappato resta `unknown`**: non si indovina, così il buco è
   visibile.

## Perché le mappature sono isolate

Le conversioni di coordinate e di tipi evento sono la causa più frequente di numeri
sbagliati: un secondo tempo non ribaltato somma due cose diverse, un asse `y` invertito
specchia tutte le analisi di fascia. Tenerle in un solo modulo puro Python le rende
verificabili con test elementari.

## Esempio

```python
from openzone.standardize.mapping import canonical_family, convert_coordinates

convert_coordinates(60.0, 40.0, source="statsbomb", target="opta")  # (50.0, 50.0)
canonical_family("statsbomb", "Carry")                              # 'carry'
```
