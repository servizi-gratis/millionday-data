# millionday-data

Repository dati per una web app MillionDAY.

Questa versione usa come fonte primaria il sito ufficiale Lotto Italia. Gli script leggono l'endpoint JSON usato dal frontend della pagina estrazioni MillionDAY e mantengono lo schema storico della repository.

## Struttura

- `index.json`: metadati globali dell'archivio
- `latest.json`: ultima estrazione disponibile
- `years/YYYY.json`: estrazioni per anno
- `stats/curiosities.json`: statistiche precomputate per il frontend
- `winners.json`: vincite 2018-2021 backfillate dai PDF ufficiali e arricchite con `draw_id`, `slot` e `extra_numbers`

## Avvio rapido

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts\bootstrap_archive.py --data-dir .
python scripts\build_stats.py --data-dir .
python scripts\enrich_winners.py --data-dir .
python scripts\validate_data.py --data-dir .
```

### Aggiornamento ordinario

```powershell
python scripts\sync_latest.py --data-dir .
python scripts\build_stats.py --data-dir .
python scripts\validate_data.py --data-dir .
```

Oppure:

```powershell
python scripts\refresh_all.py --data-dir .
```

Se vuoi rigenerare anche l'arricchimento dei vincitori:

```powershell
python scripts\refresh_all.py --data-dir . --with-winners
```

## Fonte dati

- Pagina ufficiale: `https://www.lotto-italia.it/millionday/estratti`
- Endpoint usato dal frontend: `https://www.lotto-italia.it/md/estrazioni-e-vincite/ultime-estrazioni-millionDay.json`
- L'archivio MillionDAY parte dal 7 febbraio 2018.
- L'EXTRA MillionDAY parte dal 16 marzo 2022.
- Oggi esistono due estrazioni giornaliere: 13:00 e 20:30.

`sync_latest.py` scarta le estrazioni non ancora pubblicate dall'API, per esempio la riga serale vuota quando il job gira prima delle 20:30. Se il dataset è rimasto fermo per qualche giorno, lo script aumenta automaticamente la finestra di recupero per colmare il buco.

## Note importanti

- I numeri principali e gli EXTRA vengono salvati sia in ordine sorgente (`numbers`, `extra_numbers`) sia ordinati (`numbers_sorted`, `extra_numbers_sorted`) per facilitare verifiche e statistiche.
- Le estrazioni più vecchie non includono `extra_numbers` e, nei periodi iniziali, è presente una sola estrazione giornaliera alle 20:30.
- `winners.json` copre **2018-2021** con backfill una tantum dai PDF ufficiali. Non fa parte del sync giornaliero.
- L'arricchimento dei vincitori fa prima un match esatto su `date + numbers`; se il PDF estratto contiene refusi OCR e in quella data esiste una sola estrazione, usa un fallback `unique_draw_same_date` marcato con confidenza `medium`.

## Formato di un record estrazione

```json
{
  "draw_id": "2026-05-12-midday",
  "date": "2026-05-12",
  "slot": "midday",
  "time": "13:00",
  "numbers": [9, 14, 22, 35, 41],
  "numbers_sorted": [9, 14, 22, 35, 41],
  "extra_numbers": [16, 18, 38, 39, 42],
  "extra_numbers_sorted": [16, 18, 38, 39, 42],
  "source": "lotto-italia.it",
  "source_url": "https://www.lotto-italia.it/millionday/estratti"
}
```

## Formato di un record vincita

```json
{
  "win_id": "2021-09-01-arezzo-ar-fi2635",
  "date": "2021-09-01",
  "amount": 1000000,
  "retailer_code": "FI2635",
  "address": "localita' indicatore zona a",
  "city": "AREZZO",
  "province": "AR",
  "region": "TOSCANA",
  "channel": "retail",
  "pdf_numbers": [2, 8, 13, 14, 19],
  "numbers": [19, 14, 2, 13, 8],
  "numbers_sorted": [2, 8, 13, 14, 19],
  "draw_id": "2021-09-01-evening",
  "slot": "evening",
  "time": "20:30",
  "extra_numbers": [],
  "match_status": "matched",
  "match_method": "exact_date_numbers",
  "match_confidence": "high"
}
```

## Workflow GitHub Actions

Il workflow incluso esegue:

1. `sync_latest.py`
2. `build_stats.py`
3. `validate_data.py`
4. commit e push se ci sono modifiche

Per il bootstrap iniziale conviene lanciare gli script in locale e poi fare il primo push del dataset popolato.
