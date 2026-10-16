# `openzone.glossary`

L'enciclopedia interna di OpenZone: definizioni, formule, fonti e generazioni, in YAML
accanto al codice invece che dentro il codice.

| File | Contenuto | Stato |
|---|---|---|
| [`metrics.yaml`](metrics.yaml) | Schede delle metriche: definizione, formula, unità, fonte, generazione, calcolabilità | bozza, 12 metriche |
| [`sources.yaml`](sources.yaml) | Schede delle fonti: accesso, licenza, ridistribuibilità, adapter | bozza, 11 fonti |
| [`opta_definitions.yaml`](opta_definitions.yaml) | Tipi evento e qualificatori Opta | **incompleto e non verificato**, per scelta |

## Perché YAML e non Python

Le definizioni devono poter essere corrette e riviste da un analista senza toccare la
logica, e devono poter essere lette anche da strumenti che non importano questa libreria
(per esempio il cruscotto OpenPitch). Sono dati, non codice.

## Onestà dei contenuti

`opta_definitions.yaml` è deliberatamente incompleto. I `type_id` presenti corrispondono
all'uso più diffuso nella documentazione pubblica, ma **non sono stati verificati sulla
fonte ufficiale**: ogni voce ha `verified: false`. La regola è che nessuna voce entra
"per sentito dire"; se non è verificata, resta fuori dal calcolo e l'evento è trattato
come sconosciuto, con un avviso. Meglio un buco dichiarato che un numero sbagliato.

Anche le licenze in `sources.yaml` sono annotazioni di lavoro, non consulenza legale, e
vanno verificate alla fonte.

L'IPO (Indice di Pericolosità Offensiva) è documentato come **non calcolabile**: la
formula è proprietaria di SICS/Coverciano. La scheda esiste per spiegare perché la metrica
non è disponibile, non per prometterla.

## API

```python
from openzone.glossary import get_glossary, metrics, sources, opta_event_types

get_glossary("xT")        # chiave canonica, alias, case-insensitive
metrics()["xg"]           # tutte le schede
sources()["pannadata"]    # licenza e limiti d'uso della fonte
opta_event_types()[16]    # tipo evento Opta 16 = Goal
```

Una metrica sconosciuta produce un errore con i nomi simili fra cui scegliere, invece di un
`KeyError` muto.
