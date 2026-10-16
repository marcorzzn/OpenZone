# Test

```bash
pytest                     # suite unit: nessuna rete, nessun file scaricato
pytest -m network          # test che scaricano dati reali (StatsBomb Open Data)
pytest --cov=openzone      # copertura
```

La configurazione in `pyproject.toml` esclude di default i test marcati `network` e
`slow`: la suite predefinita gira offline e in pochi secondi.

## Come sono scritti

La fixture principale (`conftest.py`) è una tabella di **10 eventi costruita a mano**,
con i valori attesi calcolabili a mente leggendo il test: squadra 1 con 3 passaggi (2
riusciti), 1 conduzione, 2 tiri (1 gol), 1 intercettazione e 1 fallo; squadra 2 con 2
passaggi. Questo permette di verificare conteggi, possesso, progressione e PPDA con
numeri che si possono ricontrollare senza eseguire nulla.

I test che usano dati reali sono separati e marcati `network`, e **non falliscono se la
rete manca**: fanno `skip` con il motivo, perché un test di integrazione non deve rendere
rossa la suite su una macchina offline.

Una parte dei test verifica che le funzioni non ancora implementate **falliscano
dichiarandolo**, invece di restituire un valore approssimato. È una scelta deliberata: la
non-implementazione è un contratto verificato, non un vuoto da riempire in silenzio.

## Ambienti con permessi restrittivi

Alcuni test usano la fixture `tmp_path` di pytest, che crea la directory temporanea con
permessi ristretti (0700). In ambienti dove un sandbox toglie al processo l'accesso alle
directory create in quel modo (per esempio un agente che esegue i test dentro una
sandbox di sistema), quei test falliscono con `PermissionError` **prima** di eseguire il
codice: è una limitazione dell'ambiente, non un difetto della libreria.

In quel caso la suite va eseguita fuori dalla sandbox. Non è utile passare
`--basetemp`: anche quella directory viene creata con gli stessi permessi.
