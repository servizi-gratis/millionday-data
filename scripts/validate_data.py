from __future__ import annotations

import argparse
from collections import Counter
from datetime import date

from common import ensure_layout, load_all_draws, load_json, winners_file

VALID_SLOTS = {"midday", "evening"}
VALID_TIMES = {"13:00", "20:30"}
VALID_RANGE = set(range(1, 56))
VALID_CHANNELS = {"retail", "online", None}
VALID_MATCH_STATUSES = {"matched", "ambiguous", "unmatched"}
VALID_MATCH_CONFIDENCE = {"high", "medium", "low", "none"}


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


def _validate_winner(record: dict, draw_ids: dict[str, dict]) -> None:
    date.fromisoformat(record["date"])
    assert int(record["amount"]) > 0, f"winner {record.get('win_id')} ha amount non positivo"
    assert record.get("channel") in VALID_CHANNELS, f"winner {record.get('win_id')} ha channel non valido"

    pdf_numbers = record.get("pdf_numbers") or record.get("numbers") or []
    assert len(pdf_numbers) == 5, f"winner {record.get('win_id')} ha pdf_numbers non validi"
    assert set(int(n) for n in pdf_numbers).issubset(VALID_RANGE), f"winner {record.get('win_id')} ha pdf_numbers fuori range"

    numbers = record.get("numbers") or []
    assert len(numbers) == 5, f"winner {record.get('win_id')} ha numbers non validi"
    assert len(set(int(n) for n in numbers)) == 5, f"winner {record.get('win_id')} ha numbers duplicati"
    assert set(int(n) for n in numbers).issubset(VALID_RANGE), f"winner {record.get('win_id')} ha numbers fuori range"

    extras = record.get("extra_numbers", [])
    assert len(extras) in {0, 5}, f"winner {record.get('win_id')} ha extra di lunghezza invalida"
    if extras:
        assert len(set(int(n) for n in extras)) == 5, f"winner {record.get('win_id')} ha extra duplicati"
        assert set(int(n) for n in extras).issubset(VALID_RANGE), f"winner {record.get('win_id')} ha extra fuori range"

    assert record.get("match_status") in VALID_MATCH_STATUSES, f"winner {record.get('win_id')} ha match_status invalido"
    assert record.get("match_confidence") in VALID_MATCH_CONFIDENCE, f"winner {record.get('win_id')} ha match_confidence invalida"

    draw_id = record.get("draw_id")
    if draw_id is None:
        assert record.get("match_status") == "unmatched", f"winner {record.get('win_id')} senza draw_id ma non unmatched"
        return

    assert draw_id in draw_ids, f"winner {record.get('win_id')} punta a draw_id inesistente {draw_id}"
    draw = draw_ids[draw_id]
    assert record.get("slot") == draw["slot"], f"winner {record.get('win_id')} slot incoerente"
    assert record.get("time") == draw["time"], f"winner {record.get('win_id')} time incoerente"
    assert record.get("date") == draw["date"], f"winner {record.get('win_id')} date incoerente"
    assert record.get("numbers_sorted") == draw.get("numbers_sorted"), f"winner {record.get('win_id')} numbers_sorted incoerente"
    assert record.get("extra_numbers_sorted", []) == draw.get("extra_numbers_sorted", []), f"winner {record.get('win_id')} extra incoerenti"


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida il dataset MillionDAY")
    parser.add_argument("--data-dir", default=".", help="Root della repo dati")
    args = parser.parse_args()

    root = ensure_layout(args.data_dir)
    draws = load_all_draws(root)
    draw_ids_counter = Counter(draw["draw_id"] for draw in draws)
    duplicates = [draw_id for draw_id, count in draw_ids_counter.items() if count > 1]
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

    winners_payload = load_json(winners_file(root), {})
    winner_records = winners_payload.get("records", [])
    assert winners_payload.get("unique_records") == len(winner_records), "winners.unique_records non coincide"
    draw_ids = {draw["draw_id"]: draw for draw in draws}
    for record in winner_records:
        _validate_winner(record, draw_ids)

    enrichment = winners_payload.get("enrichment", {})
    if winner_records and enrichment:
        exact = enrichment.get("exact_matches", 0)
        date_only = enrichment.get("date_only_matches", 0)
        overlap = enrichment.get("overlap_matches", 0)
        ambiguous = enrichment.get("ambiguous", 0)
        unmatched = enrichment.get("unmatched", 0)
        assert exact + date_only + overlap + ambiguous + unmatched == len(winner_records), "conteggi enrichment incoerenti"

    print(f"Archivio valido: {len(draws)} estrazioni, anni {years}, winners {len(winner_records)}")


if __name__ == "__main__":
    main()
