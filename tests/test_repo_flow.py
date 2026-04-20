from pathlib import Path

from common import ensure_layout, load_all_draws, refresh_index_and_latest, upsert_draws


def test_upsert_and_refresh(tmp_path: Path) -> None:
    root = ensure_layout(tmp_path)
    initial = []
    incoming = [
        {
            "draw_id": "2026-04-19-midday",
            "date": "2026-04-19",
            "slot": "midday",
            "time": "13:00",
            "numbers": [4, 26, 32, 40, 43],
            "numbers_sorted": [4, 26, 32, 40, 43],
            "extra_numbers": [3, 29, 37, 42, 50],
            "extra_numbers_sorted": [3, 29, 37, 42, 50],
            "source": "millionday.cloud",
            "source_url": "https://www.millionday.cloud/archivio-estrazioni.php",
        },
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
            "source_url": "https://www.millionday.cloud/archivio-estrazioni.php",
        },
    ]
    merged, changes = upsert_draws(initial, incoming)
    assert changes == 2
    refresh_index_and_latest(root, merged)

    all_draws = load_all_draws(root)
    assert len(all_draws) == 2
    assert all_draws[-1]["draw_id"] == "2026-04-19-evening"
