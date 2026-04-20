import json
import subprocess
import sys
from pathlib import Path

from common import dump_json, ensure_layout, refresh_index_and_latest


def test_enrich_winners_exact_and_date_fallback(tmp_path: Path) -> None:
    root = ensure_layout(tmp_path)
    draws = [
        {
            "draw_id": "2020-01-14-evening",
            "date": "2020-01-14",
            "slot": "evening",
            "time": "20:30",
            "numbers": [31, 4, 18, 25, 20],
            "numbers_sorted": [4, 18, 20, 25, 31],
            "extra_numbers": [],
            "extra_numbers_sorted": [],
            "source": "millionday.cloud",
            "source_url": "https://www.millionday.cloud/archivio-estrazioni.php",
        },
        {
            "draw_id": "2021-09-01-evening",
            "date": "2021-09-01",
            "slot": "evening",
            "time": "20:30",
            "numbers": [19, 14, 2, 13, 8],
            "numbers_sorted": [2, 8, 13, 14, 19],
            "extra_numbers": [],
            "extra_numbers_sorted": [],
            "source": "millionday.cloud",
            "source_url": "https://www.millionday.cloud/archivio-estrazioni.php",
        },
    ]
    refresh_index_and_latest(root, draws)
    winners_payload = {
        "updated_at": "2026-04-20T00:00:00Z",
        "source": "official_pdf_backfill_2018_2021",
        "raw_records": 2,
        "unique_records": 2,
        "duplicate_rows_removed": 0,
        "years": [2020, 2021],
        "counts_by_year": {"2020": 1, "2021": 1},
        "records": [
            {
                "win_id": "a",
                "date": "2020-01-14",
                "amount": 1000000,
                "retailer_code": "RM6835",
                "address": "via dei fienili",
                "city": "ROMA",
                "province": "RM",
                "region": "LAZIO",
                "channel": "retail",
                "numbers": [1, 18, 20, 25, 31],
                "source_type": "official_pdf",
                "source_year": 2020,
                "source_file": "vincite-millionday-2020.pdf",
                "source_url": "https://example.test/2020.pdf",
                "duplicate_count": 1,
            },
            {
                "win_id": "b",
                "date": "2021-09-01",
                "amount": 1000000,
                "retailer_code": "FI2635",
                "address": "localita' indicatore zona a",
                "city": "AREZZO",
                "province": "AR",
                "region": "TOSCANA",
                "channel": "retail",
                "numbers": [2, 8, 13, 14, 19],
                "source_type": "official_pdf",
                "source_year": 2021,
                "source_file": "vincite-millionday-2021.pdf",
                "source_url": "https://example.test/2021.pdf",
                "duplicate_count": 1,
            },
        ],
    }
    dump_json(root / "winners.json", winners_payload)

    subprocess.run([sys.executable, str(Path('scripts/enrich_winners.py').resolve()), '--data-dir', str(root)], check=True)

    enriched = json.load((root / 'winners.json').open('r', encoding='utf-8'))
    records = {item['win_id']: item for item in enriched['records']}
    assert records['a']['draw_id'] == '2020-01-14-evening'
    assert records['a']['match_method'] == 'unique_draw_same_date'
    assert records['a']['resolved_from_pdf_numbers'] is True
    assert records['b']['draw_id'] == '2021-09-01-evening'
    assert records['b']['match_method'] == 'exact_date_numbers'
    assert records['b']['resolved_from_pdf_numbers'] is False
