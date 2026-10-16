# OpenZone

**Motore Python open source per trasformare dati calcistici grezzi ed eterogenei in
dataset puliti, standardizzati e arricchiti con metriche avanzate.**

OpenZone è la **libreria**. [OpenPitch](#) sarà il **cruscotto**: OpenPitch importa
OpenZone, mai il contrario. OpenZone è testabile in isolamento e pubblicabile su PyPI.

> Stato: **0.1.0 – pre-alpha**. Lo scheletro dei moduli è completo; le implementazioni
> sono in corso secondo la [roadmap](OPENZONE_BLUEPRINT.md#8-roadmap).

Il documento di riferimento è [OPENZONE_BLUEPRINT.md](OPENZONE_BLUEPRINT.md).

## Installazione

Il pacchetto non è ancora pubblicato su PyPI. In sviluppo:

```bash
git clone https://github.com/marcorzzn/OpenZone
cd OpenZone
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev]"
```

Le dipendenze pesanti sono divise in extra, così un analista che usa solo il
glossario o la cache non scarica `mplsoccer` o `duckdb`:

| Extra | Contenuto |
|-------|-----------|
| `ingest` | `requests`, `soccerdata`, `ScraperFC`, `statsbombpy`, `pyarrow` |
| `standardize` | `kloppy`, `socceraction` |
| `warehouse` | `duckdb` |
| `spatial` | `networkx` |
| `viz` | `mplsoccer`, `matplotlib` |
| `dev` | `pytest`, `pytest-cov`, `ruff`, `mypy` |

Solo le dipendenze core (`pandas`, `numpy`, `PyYAML`) sono obbligatorie, e
`import openzone` funziona anche senza di esse: gli import pesanti sono pigri.

## Moduli

| Modulo | Scopo |
|--------|-------|
| [`openzone.ingest`](openzone/ingest/README.md) | Acquisizione dati da fonti esterne |
| [`openzone.standardize`](openzone/standardize/README.md) | Uniformare eventi e tracking data |
| [`openzone.warehouse`](openzone/warehouse/README.md) | Storage locale e cache su disco |
| [`openzone.metrics`](openzone/metrics/README.md) | Metriche calcistiche, per generazione |
| [`openzone.glossary`](openzone/glossary/README.md) | Enciclopedia di metriche, eventi e fonti |
| [`openzone.spatial`](openzone/spatial/README.md) | Analisi spaziale (Soccermatics) |
| [`openzone.models`](openzone/models/README.md) | Modelli di possesso, clustering, simulazione |
| [`openzone.api`](openzone/api/README.md) | Superficie pubblica stabile |
| [`openzone.viz`](openzone/viz/README.md) | Visualizzazione statica (mplsoccer) |

## Uso

```python
import openzone

openzone.__version__

# Glossario: definizione, formula, fonte e generazione di una metrica
from openzone.glossary import get_glossary

get_glossary("xT")

# Contratti pubblici (le implementazioni arrivano con la roadmap)
from openzone.api import load_shots, compute_xg
```

## Test

```bash
pytest                       # unit test, nessuna rete
pytest -m network            # test che scaricano dati reali (StatsBomb Open Data)
pytest --cov=openzone
```

## Licenza

Il codice è distribuito con licenza [MIT](LICENSE). I **dati** non sono coperti da
questa licenza: ogni fonte ha la sua. Vedi la nota in fondo a [LICENSE](LICENSE) e
il file [`sources.yaml`](openzone/glossary/sources.yaml).
