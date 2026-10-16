# OpenZone – Blueprint e Manifesto

**Versione:** 0.1 (bozza)  
**Data:** 16 ottobre 2026  
**Autore:** @sscnapolidata  
**Repository:** `github.com/marcorzzn/OpenZone`  
**Documento:** `OPENZONE_BLUEPRINT.md`

---

## 1. Visione

OpenZone è una **libreria Python open source** che trasforma dati calcistici grezzi, sparsi e provenienti da fonti eterogenee in **dataset puliti, standardizzati e arricchiti con metriche avanzate**.  

L’obiettivo è dare a analisti, data scientist e sviluppatori un **motore unico** per:

- Ingestione multi-fonte (Opta, StatsBomb, Understat, FBref, WhoScored, ecc.)
- Standardizzazione di eventi e tracking data
- Calcolo di metriche (xG, xA, xGOT, IPO, xT, PPDA, progressive passes, packing, pitch control)
- Analisi spaziale (pass networks, triangoli, half-spaces, zone di pressing)
- Esportazione di report statici (mplsoccer)

OpenZone è il **motore**. OpenPitch è il **cruscotto** (UI interattiva).  
OpenPitch importa OpenZone. OpenZone non sa nulla di OpenPitch.

---

## 2. Obiettivi

1. **Unificare l’accesso ai dati calcistici** – superare la frammentazione di formati e provider.
2. **Standardizzare gli eventi** – usare kloppy per uniformare Opta, StatsBomb, Wyscout.
3. **Calcolare metriche avanzate** – implementare xG, xA, xGOT, IPO, xT, PPDA, packing, pitch control.
4. **Fornire un glossario integrato** – definizioni Opta, formule, fonti, generazioni.
5. **Abilitare analisi spaziali** – ispirate a Soccermatics: pass networks, triangoli, zone.
6. **Essere riutilizzabile** – pubblicabile su PyPI (`pip install openzone`).
7. **Rispettare le licenze** – chiarezza su ToS e fonti.
8. **Documentare tutto** – ogni metrica, ogni modulo, ogni scelta.

---

## 3. Architettura di alto livello

```
┌────────────────────────────────────────────────────────┐
│  OpenPitch (applicazione)                              │
│  UI interattiva, drag-and-drop, chat LLM, 2D/3D        │
│  Dipende da: openzone.api, openzone.viz                │
└────────────────────────────────────────────────────────┘
                          │
                          │ importa
                          ▼
┌────────────────────────────────────────────────────────┐
│  OpenZone (libreria Python)                            │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ │
│  │ ingest   │ │ standard. │ │ warehouse │ │ metrics │ │
│  └──────────┘ └───────────┘ └───────────┘ └─────────┘ │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ │
│  │ glossary │ │ spatial   │ │ models    │ │ api     │ │
│  └──────────┘ └───────────┘ └───────────┘ └─────────┘ │
│  ┌──────────┐                                          │
│  │ viz      │                                          │
│  └──────────┘                                          │
└────────────────────────────────────────────────────────┘
```

**Relazione:** OpenPitch → OpenZone (unidirezionale).  
**Versioning:** OpenPitch blocca una versione stabile di OpenZone.  
**Disaccoppiamento:** OpenZone è testabile in isolamento, pubblicabile su PyPI.

---

## 4. Moduli di OpenZone

### 4.1 `ingest/`

Scopo: acquisire dati da fonti esterne.

| Sottomodulo | Fonte | Libreria | Note |
|-------------|-------|----------|------|
| `pannadata.py` | Opta (Parquet) | `pandas`, `pyarrow` | Serie A dal 2013. Licenza incerta. |
| `soccerdata.py` | FBref, Understat, WhoScored, FotMob, Sofascore, SoFIFA, ESPN, Club Elo, Football-Data.co.uk | `soccerdata` | DataFrame allineati. ToS vari. |
| `scraperfc.py` | Varie | `ScraperFC` | Fallback. ToS vari. |
| `statsbomb.py` | StatsBomb Open Data | `statsbombpy` o parsing JSON | Serie A 2015/16. |
| `understat.py` | Understat | `soccerdata` | xG, shot map. |
| `whoscored.py` | WhoScored | `soccerdata` | Descrizioni eventi. |
| `datahub.py` | DataHub | `pandas` | Solo match-level. |
| `football_data_org.py` | football-data.org | `requests` | Calendario, risultati. |

### 4.2 `standardize/`

Scopo: uniformare formati di eventi e tracking.

| Sottomodulo | Libreria | Descrizione |
|-------------|----------|-------------|
| `kloppy.py` | `kloppy` | Converte Opta, StatsBomb, Wyscout in formato standard. |
| `socceraction.py` | `socceraction` | Converte eventi in SPADL. |
| `mapping.py` | – | Mapping tra event type ID e nomi standard. |

### 4.3 `warehouse/`

Scopo: memorizzare dati localmente per evitare riscaricamenti.

| Sottomodulo | Tecnologia | Descrizione |
|-------------|------------|-------------|
| `duckdb.py` | DuckDB | Warehouse colonnare per Parquet e DataFrame. |
| `cache.py` | – | Cache su disco con hash delle query. |

### 4.4 `metrics/`

Scopo: calcolare metriche calcistiche.

| Sottomodulo | Metriche | Generazione |
|-------------|----------|-------------|
| `basic.py` | Gol, assist, tiri, possesso, key passes | 1ª |
| `advanced.py` | xG, xA, xGOT, IPO, big chances | 2ª |
| `predictive.py` | xT, PPDA, progressive passes/carries, packing | 3ª |
| `socceraction.py` | VAEP, xT (SPADL) | 3ª |

### 4.5 `glossary/`

Scopo: enciclopedia interna delle metriche e degli eventi.

| File | Contenuto |
|------|-----------|
| `opta_definitions.yaml` | Definizioni Opta: eventi, qualificatori, metriche |
| `metrics.yaml` | Definizioni xG, xA, xGOT, IPO, xT, PPDA, ecc. |
| `sources.yaml` | Fonti, URL, licenze, limiti |

### 4.6 `spatial/`

Scopo: analisi spaziale ispirata a Soccermatics.

| Sottomodulo | Descrizione |
|-------------|-------------|
| `pass_networks.py` | Grafi di passaggi (networkx). |
| `triangles.py` | Triangoli di passaggio. |
| `half_spaces.py` | Analisi half-spaces e corridoi. |
| `pressing_zones.py` | Zone di pressing, PPDA per zona. |
| `pitch_control.py` | Pitch control, TDA, packing. |

### 4.7 `models/`

Scopo: modelli predittivi e di possesso.

| Sottomodulo | Descrizione |
|-------------|-------------|
| `possession.py` | Modelli di possesso. |
| `clustering.py` | Clustering di azioni. |
| `simulation.py` | Simulazioni di partita. |

### 4.8 `api/`

Scopo: funzioni pubbliche per OpenPitch e utenti.

```python
# Esempi
load_shots(player_id, season)
load_events(match_id)
compute_xg(shots_df)
compute_xt(events_df)
get_glossary(metric)
plot_shot_map(shots_df)
```

### 4.9 `viz/`

Scopo: visualizzazione statica.

| Sottomodulo | Libreria | Descrizione |
|-------------|----------|-------------|
| `pitch.py` | `mplsoccer` | Disegno campo. |
| `shots.py` | `mplsoccer`, `matplotlib` | Mappe tiri. |
| `passes.py` | `mplsoccer`, `networkx` | Pass networks, frecce. |

---

## 5. Risorse e dipendenze

### 5.1 Dati

| Risorsa | Tipo | Utilizzo | Limiti |
|---------|------|----------|--------|
| **pannadata** | Opta Parquet | Serie A 2013–2026 | Licenza incerta |
| **StatsBomb Open Data** | Eventi JSON | Serie A 2015/16 | Solo una stagione |
| **Understat** | xG, shot map | Tiri, xG | No passaggi |
| **FBref** | Statistiche | Aggregate | No coordinate passaggi |
| **WhoScored** | Descrizioni eventi | Tipo assist | ToS vietano scraping |
| **Sofascore** | Shotmap | x/y, xGOT | ToS vietano scraping |
| **Opta Event Definitions** | Documento | Glossario | Non dataset |
| **Sportmonks Glossary** | Glossario | Metriche | A pagamento |
| **SICS/Coverciano IPO** | Metrica | IPO | Formula proprietaria |

### 5.2 Librerie

| Libreria | Ruolo | Modulo |
|----------|-------|--------|
| `soccerdata` | Scraper multi-fonte | `ingest` |
| `ScraperFC` | Scraper fallback | `ingest` |
| `kloppy` | Standardizzazione | `standardize` |
| `socceraction` | SPADL, VAEP | `metrics` |
| `soccermatics` (R) | Analisi spaziale | `spatial` (via `rpy2` o reimplementazione) |
| `mplsoccer` | Visualizzazione | `viz` |
| `networkx` | Grafi | `spatial` |
| `duckdb` | Warehouse | `warehouse` |
| `pandas`, `numpy` | Manipolazione dati | ovunque |
| `matplotlib` | Grafica | `viz` |

### 5.3 Contesto

| Risorsa | Utilizzo |
|---------|----------|
| `pythonfootball.com` articolo xG | Guida scelta modello xG |
| BBC article | Inquadramento |
| Soccermatics libro | Concetti spaziali |
| Wikipedia Sports analytics | Contesto |

---

## 6. Data Model e contratti API

### 6.1 Entità principali

| Entità | Campi minimi |
|--------|--------------|
| `Match` | `match_id`, `date`, `competition`, `home_team`, `away_team` |
| `Player` | `player_id`, `name`, `team`, `position` |
| `Event` | `event_id`, `match_id`, `minute`, `second`, `type_id`, `player_id`, `x`, `y`, `end_x`, `end_y`, `qualifiers` |
| `Shot` | `shot_id`, `match_id`, `player_id`, `x`, `y`, `xg`, `outcome` |
| `Metric` | `metric_id`, `name`, `value`, `generation`, `source` |

### 6.2 Contratti API (esempi)

```python
# openzone/api/__init__.py

def load_shots(player_id: int, season: str) -> pd.DataFrame:
    """Restituisce tutti i tiri di un giocatore in una stagione."""

def load_events(match_id: int) -> pd.DataFrame:
    """Restituisce tutti gli eventi di una partita."""

def compute_xg(shots: pd.DataFrame) -> pd.Series:
    """Calcola xG per ogni tiro."""

def compute_xt(events: pd.DataFrame) -> pd.Series:
    """Calcola xT per ogni evento."""

def get_glossary(metric: str) -> dict:
    """Restituisce definizione, formula, fonte, generazione."""
```

---

## 7. Glossario delle metriche (estratto)

| Metrica | Generazione | Formula / Descrizione | Fonte |
|---------|-------------|------------------------|-------|
| **xG** | 2ª | Probabilità che un tiro diventi gol | Opta, Understat |
| **xA** | 2ª | Probabilità che un passaggio diventi assist | Opta |
| **xGOT** | 2ª | Qualità del tiro dopo il tiro | Opta |
| **IPO** | 2ª | Indice di Pericolosità Offensiva | SICS/Coverciano |
| **xT** | 3ª | Expected Threat | Karun Singh |
| **PPDA** | 3ª | Passes Per Defensive Action | Opta |
| **Progressive Passes** | 3ª | Avanzamento ≥ 10 m | Opta |
| **Packing** | 3ª | Numero di avversari superati | – |
| **Pitch Control** | 3ª | Probabilità di controllo palla | – |
| **Big Chances** | 2ª | Occasioni chiare | Opta |

---

## 8. Roadmap

### Fase 1 – Fondamenta (mese 1)
- [ ] Creare struttura package `openzone/`
- [ ] Implementare `ingest/soccerdata.py` e `ingest/pannadata.py`
- [ ] Implementare `warehouse/duckdb.py`
- [ ] Definire `glossary/opta_definitions.yaml`
- [ ] Scrivere test con StatsBomb Open Data

### Fase 2 – Metriche (mese 2)
- [ ] Implementare `metrics/basic.py`
- [ ] Implementare `metrics/advanced.py` (xG, xA, xGOT)
- [ ] Integrare `socceraction` per xT e VAEP
- [ ] Documentare ogni metrica nel glossario

### Fase 3 – Spaziale (mese 3)
- [ ] Reimplementare Soccermatics in Python
- [ ] Implementare `spatial/pass_networks.py`
- [ ] Implementare `spatial/half_spaces.py`
- [ ] Implementare `spatial/pressing_zones.py`

### Fase 4 – API e visualizzazione (mese 4)
- [ ] Definire `api/` pubblica
- [ ] Implementare `viz/pitch.py`, `viz/shots.py`, `viz/passes.py`
- [ ] Pubblicare su PyPI (`pip install openzone`)

### Fase 5 – Integrazione OpenPitch (mese 5)
- [ ] Definire sidecar Python per OpenPitch
- [ ] Esportare API REST locale
- [ ] Testare integrazione UI

---

## 9. Linee guida per contribuire

- **Codice:** PEP 8, type hints, docstring Google style.
- **Test:** pytest, coverage > 80%.
- **Documentazione:** ogni modulo ha un README; ogni metrica ha una scheda nel glossario.
- **Versioning:** semantic versioning (SemVer).
- **Licenza:** MIT (da definire).
- **ToS:** non includere dati di fonti che vietano la redistribuzione.

---

## 10. Licenza e note legali

- **OpenZone** è distribuito con licenza MIT.
- **Dati:** ogni fonte ha la sua licenza. Non redistribuire dati di Opta, StatsBomb, Wyscout senza permesso.
- **Scraping:** `soccerdata` e `ScraperFC` fanno scraping. Verificare i ToS delle fonti.
- **pannadata:** licenza non specificata. Usare con cautela.
- **Sofascore:** ToS vietano scraping. Non usare in produzione.

---

## 11. Appendice – Risorse dettagliate

### 11.1 Fonti dati

| Nome | URL | Tipo | Licenza |
|------|-----|------|---------|
| pannadata | github.com/peteowen1/pannadata | Opta Parquet | Incerta |
| StatsBomb Open Data | github.com/statsbomb/open-data | Eventi JSON | Open |
| Understat | understat.com | xG, shot map | – |
| FBref | fbref.com | Statistiche | ToS |
| WhoScored | whoscored.com | Eventi | ToS |
| Sofascore | sofascore.com | Shotmap | ToS |
| Opta Event Definitions | statsperform.com/opta-event-definitions/ | Documento | – |
| Sportmonks Glossary | sportmonks.com | Glossario | – |

### 11.2 Librerie

| Nome | URL | Ruolo |
|------|-----|-------|
| soccerdata | soccerdata.readthedocs.io | Scraper |
| ScraperFC | github.com/oseymour/ScraperFC | Scraper |
| kloppy | github.com/PySport/kloppy | Standardizzazione |
| socceraction | github.com/PySport/socceraction | Metriche |
| soccermatics | github.com/DavidSumpter/soccermatics | Spaziale (R) |
| mplsoccer | github.com/andrewRowlinson/mplsoccer | Visualizzazione |
| networkx | networkx.org | Grafi |
| duckdb | duckdb.org | Warehouse |

### 11.3 Contesto

| Nome | URL |
|------|-----|
| pythonfootball.com – Which xG data should you trust | pythonfootball.com |
| BBC – Data in football | bbc.com/news/science-environment-37327939 |
| Soccermatics libro | – |
| Wikipedia Sports analytics | en.wikipedia.org/wiki/Sports_analytics |

---

## 12. DSH

Questo blueprint è redatto in Markdown e può essere integrato in qualsiasi sistema di documentazione, incluso **DSH**.  
La struttura a moduli, le tabelle e i contratti API sono pensati per essere facilmente parsati e visualizzati.

---

**Fine del blueprint.**  
Per contribuire: aprire una issue o una pull request su GitHub.
