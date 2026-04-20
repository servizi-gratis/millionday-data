from __future__ import annotations

import argparse
from collections import Counter
from datetime import date

from common import ensure_layout, load_all_draws, load_json

VALID_SLOTS = {"midday", "evening"}
VALID_TIMES = {"13:00", "20:30"}
VALID_RANGE = set(range(1, 56))


def _validate_draw(draw: dict) -> None:
    date.fromisoformat(draw["date"])
    assert draw["slot"] in VALID_SLOTS, f"slot non valida: {draw['slot']}"
    assert draw["time"] in VALID_TIMES, f"orario non valido: {draw['time']}"
    assert len(draw["numbers"]) == 5, f"draw {draw['draw_id']} ha {len(draw['numbers'])} numeri principali"
    assert len(set(draw["numbers"])) == 5, f"draw {draw['draw_id']} ha numeri principali duplicati"
    assert set(draw["numbers"]).issubset(VALID_RANGE), f"draw {draw['draw_id']} ha numeri fuori range"
    extras = draw.get("extra_numbers", [])
    assert len(extras) in {0, 5}, f"draw {draw['draw_id']} ha extra di lunghezza invalida"
    if extras:
        assert len(set(extras)) == 5, f"draw {draw['draw_id']} ha extra duplicati"
        assert set(extras).issubset(VALID_RANGE), f"draw {draw['draw_id']} ha extra fuori range"


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida il dataset MillionDAY")
    parser.add_argument("--data-dir", default=".", help="Root della repo dati")
    args = parser.parse_args()

    root = ensure_layout(args.data_dir)
    draws = load_all_draws(root)
    draw_ids = Counter(draw["draw_id"] for draw in draws)
    duplicates = [draw_id for draw_id, count in draw_ids.items() if count > 1]
    assert not duplicates, f"draw_id duplicati: {duplicates[:10]}"

    for draw in draws:
        _validate_draw(draw)

    index = load_json(root / "index.json", {})
    latest = load_json(root / "latest.json", {})
    years = index.get("years", [])
    assert index.get("total_draws") == len(draws), "index.total_draws non coincide"
    assert years == sorted(years), "index.years non ordinato"
    if draws:
        assert latest.get("draw", {}).get("draw_id") == draws[-1]["draw_id"], "latest.json non punta all'ultima estrazione"

    print(f"Archivio valido: {len(draws)} estrazioni, anni {years}")


if __name__ == "__main__":
    main()
