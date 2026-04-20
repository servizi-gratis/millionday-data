# millionday-data

Repository dati per una web app MillionDAY.

Questa versione usa come fonte primaria la pagina archivio di `millionday.cloud`, che espone in HTML l'archivio storico delle estrazioni dal 7 febbraio 2018. Il sito ufficiale Lotto Italia conferma che l'archivio MillionDAY parte dal 7 febbraio 2018 e che oggi esistono due estrazioni giornaliere alle 13:00 e alle 20:30.

## Struttura

- `index.json`: metadati globali dell'archivio
- `latest.json`: ultima estrazione disponibile
- `years/YYYY.json`: estrazioni per anno
- `stats/curiosities.json`: statistiche precomputate per il frontend
- `winners.json`: placeholder per pipeline future sulle vincite

## Avvio rapido

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts\bootstrap_archive.py --data-dir .
python scripts\build_stats.py --data-dir .
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

## Note importanti

- La fonte primaria è **terza** e non ufficiale. È pratica e stabile per l'estrazione server-side, ma non sostituisce una fonte ufficiale.
- I numeri principali e gli EXTRA vengono salvati sia in ordine originale (`numbers`, `extra_numbers`) sia ordinati (`numbers_sorted`, `extra_numbers_sorted`) per facilitare verifiche e statistiche.
- Le estrazioni più vecchie non includono `extra_numbers` e, in alcuni periodi iniziali, è presente una sola estrazione giornaliera alle 20:30.

## Formato di un record

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

## Workflow GitHub Actions

Il workflow incluso esegue:

1. `sync_latest.py`
2. `build_stats.py`
3. `validate_data.py`
4. commit e push se ci sono modifiche

Per il bootstrap iniziale conviene lanciare gli script in locale e poi fare il primo push del dataset popolato.
