# millionday-data

Repository dati per una web app MillionDAY.

Questa versione usa come fonte primaria la pagina archivio di `millionday.cloud`, che espone in HTML l'archivio storico delle estrazioni dal 7 febbraio 2018. Il sito ufficiale Lotto Italia conferma che l'archivio MillionDAY parte dal 7 febbraio 2018 e che oggi esistono due estrazioni giornaliere alle 13:00 e alle 20:30.

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
.venv\Scriptsctivate
pip install -r requirements.txt
python scriptsootstrap_archive.py --data-dir .
python scriptsuild_stats.py --data-dir .
python scripts\enrich_winners.py --data-dir .
python scriptsalidate_data.py --data-dir .
```

### Aggiornamento ordinario

```powershell
python scripts\sync_latest.py --data-dir .
python scriptsuild_stats.py --data-dir .
python scriptsalidate_data.py --data-dir .
```

Oppure:

```powershell
python scriptsefresh_all.py --data-dir .
```

Se vuoi rigenerare anche l'arricchimento dei vincitori:

```powershell
python scriptsefresh_all.py --data-dir . --with-winners
```

## Note importanti

- La fonte primaria delle estrazioni è **terza** e non ufficiale. È pratica e stabile per l'estrazione server-side, ma non sostituisce una fonte ufficiale.
- `winners.json` copre **2018-2021** con backfill una tantum dai PDF ufficiali. Non fa parte del sync giornaliero.
- I numeri principali e gli EXTRA vengono salvati sia in ordine originale (`numbers`, `extra_numbers`) sia ordinati (`numbers_sorted`, `extra_numbers_sorted`) per facilitare verifiche e statistiche.
- Le estrazioni più vecchie non includono `extra_numbers` e, in alcuni periodi iniziali, è presente una sola estrazione giornaliera alle 20:30.
- L'arricchimento dei vincitori fa prima un match esatto su `date + numbers`; se il PDF estratto contiene refusi OCR e in quella data esiste una sola estrazione, usa un fallback `unique_draw_same_date` marcato con confidenza `medium`.

## Formato di un record estrazione

```json
{
  "draw_id": "2026-04-19-evening",
  "date": "2026-04-19",
  "slot": "evening",
  "time": "20:30",
  "numbers": [6, 36, 41, 47, 54],
  "numbers_sorted": [6, 36, 41, 47, 54],
  "extra_numbers": [19, 21, 28, 30, 35],
  "extra_numbers_sorted": [19, 21, 28, 30, 35],
  "source": "millionday.cloud",
  "source_url": "https://www.millionday.cloud/archivio-estrazioni.php"
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
