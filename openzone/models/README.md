# `openzone.models`

I moduli che *stimano* invece di misurare. Consumano l'output degli altri moduli e non lo
modificano.

| Modulo | Ruolo | Dipendenze | Stato |
|---|---|---|---|
| [`possession.py`](possession.py) | Sequenze di possesso | `pandas` | Fase 2 |
| [`clustering.py`](clustering.py) | Tipologie di giocata | `scikit-learn` (extra `models`) | Fase 3 |
| [`simulation.py`](simulation.py) | Simulazione di scenari | `numpy` | Fase 3 |

## Perché esiste questo modulo, e perché è separato

Il possesso è la variabile più mal definita dell'analisi calcistica: quasi tutte le
metriche di sequenza (key passes, xA, VAEP) dipendono dal sapere chi aveva il pallone e
quando la sequenza è finita, e ogni provider lo definisce a modo suo. Mettere questa
responsabilità in un modulo a sé rende esplicito che è una **scelta**, con parametri, e
non un dettaglio implementativo nascosto dentro `metrics`.

Le dipendenze più pesanti (`scikit-learn`) stanno in un extra separato: chi vuole solo
misurare non le installa.

## Regole più severe per la simulazione

Una simulazione produce risultati credibili anche quando sono sbagliati. Quindi: ogni
simulazione dichiara le assunzioni e distingue i parametri stimati da quelli scelti a
mano, ogni risultato è accompagnato da un intervallo e non da un numero singolo, e il seme
del generatore casuale è sempre fissato. Nessun output di questo modulo va presentato come
previsione di una partita reale.
