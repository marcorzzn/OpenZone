# `openzone.viz`

Visualizzazione statica con `mplsoccer`, per report e pubblicazioni.

| Modulo | Ruolo | Stato |
|---|---|---|
| [`pitch.py`](pitch.py) | Disegno del campo e dimensioni | Fase 4 |
| [`shots.py`](shots.py) | Mappe di tiro | Fase 4 |
| [`passes.py`](passes.py) | Reti di passaggio e frecce | Fase 4 |

Richiede l'extra `viz` (`mplsoccer`, `matplotlib`).

## Convenzioni

* campo orientato con l'attacco verso destra, coordinate normalizzate 100x100, così i
  grafici sono confrontabili con i numeri delle metriche;
* le funzioni **restituiscono** la figura invece di salvarla: chi le usa decide formato e
  destinazione, e nei test si può verificare che la figura sia stata costruita senza
  scrivere file;
* le funzioni non chiamano `show()`;
* ogni grafico che mostra un valore stimato riporta nel titolo la fonte o il modello che
  l'ha prodotto. `viz.shots.shot_map` **rifiuta** di disegnare un xG senza `model_label`:
  un grafico è la forma più facile in cui un numero senza provenienza finisce in una
  presentazione.

## Regole di leggibilità

* una sola codifica per volta: la dimensione dei pallini rappresenta l'xG *oppure* il
  numero di tiri, non entrambe;
* nelle reti di passaggio i pesi vanno normalizzati per i minuti giocati, altrimenti il
  grafico mostra chi è rimasto in campo più a lungo;
* non più di venti archi in una rete (`viz.passes.MAX_EDGES`): oltre, il grafico diventa
  una ragnatela e non comunica più nulla.
