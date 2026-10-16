# `openzone.api`

La superficie pubblica di OpenZone: **tutto ciò che un'applicazione esterna deve usare**.

```python
from openzone.api import compute_xg, get_glossary, load_events, load_shots, plot_shot_map
```

## Contratto di stabilità

* **`openzone.api` è stabile**: i nomi e le firme di questo modulo cambiano solo con un
  aumento di versione maggiore, e ogni cambio viene prima deprecato.
* **i sottomoduli sono interni**: `openzone.metrics`, `openzone.spatial` e simili possono
  cambiare fra versioni minori. Un'applicazione che li importa direttamente si assume il
  costo di seguirne l'evoluzione.

Questa separazione esiste perché OpenPitch deve poter fissare una versione di OpenZone e
aggiornarla quando vuole, non quando OpenZone cambia idea su un nome.

## Stato

| Funzione | Stato |
|---|---|
| `get_glossary(metric)` | **usabile** |
| `load_shots(player_id, season)` | firma congelata, pipeline in Fase 1 |
| `load_events(match_id)` | firma congelata, pipeline in Fase 1 |
| `compute_xg(shots)` | modello in Fase 2 |
| `compute_xt(events)` | modello in Fase 2-3 |
| `plot_shot_map(shots)` | Fase 4 |

Le firme sono congelate prima delle implementazioni, di proposito: sono il contratto che
OpenPitch usa per sviluppare in parallelo, e cambiarle dopo costerebbe il doppio.

## Nota per gli utenti esterni

Se ti serve qualcosa che qui non c'è, la strada giusta è aggiungerla a questo modulo con
una firma stabile, non importare un sottomodulo interno. Il secondo è più veloce oggi e più
costoso al primo aggiornamento.
