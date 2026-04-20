from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date
from typing import Any

from common import (
    ROOT_SOURCE_NAME,
    ROOT_SOURCE_URL,
    canonical_number_key,
    dump_json,
    ensure_layout,
    load_all_draws,
    load_json,
    utc_now_iso,
    winners_file,
)


def build_draw_indexes(draws: list[dict[str, Any]]) -> tuple[dict[tuple[str, tuple[int, ...]], list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    by_date_numbers: dict[tuple[str, tuple[int, ...]], list[dict[str, Any]]] = defaultdict(list)
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for draw in draws:
        by_date_numbers[(draw["date"], canonical_number_key(draw["numbers_sorted"]))].append(draw)
        by_date[draw["date"]].append(draw)
    return dict(by_date_numbers), dict(by_date)


def enrich_record(record: dict[str, Any], by_date_numbers: dict, by_date: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    enriched = deepcopy(record)
    pdf_numbers = record.get("pdf_numbers") or record.get("numbers") or []
    pdf_numbers_sorted = list(canonical_number_key(pdf_numbers))
    enriched["pdf_numbers"] = [int(n) for n in pdf_numbers]
    enriched["pdf_numbers_sorted"] = pdf_numbers_sorted

    matches = by_date_numbers.get((record["date"], tuple(pdf_numbers_sorted)), [])
    match_status = "unmatched"
    match_method = "none"
    match_confidence = "none"
    matched_draw: dict[str, Any] | None = None

    if len(matches) == 1:
        matched_draw = matches[0]
        match_status = "matched"
        match_method = "exact_date_numbers"
        match_confidence = "high"
    elif len(matches) > 1:
        match_status = "ambiguous"
        match_method = "multiple_draws_same_date_numbers"
        match_confidence = "low"
    else:
        same_day = by_date.get(record["date"], [])
        if len(same_day) == 1:
            matched_draw = same_day[0]
            match_status = "matched"
            match_method = "unique_draw_same_date"
            match_confidence = "medium"
        elif len(same_day) > 1:
            scored = []
            pdf_set = set(pdf_numbers_sorted)
            for draw in same_day:
                overlap = len(pdf_set & set(draw.get("numbers_sorted", [])))
                scored.append((overlap, draw))
            scored.sort(key=lambda item: (-item[0], item[1]["time"]))
            if scored and scored[0][0] >= 4 and (len(scored) == 1 or scored[0][0] > scored[1][0]):
                matched_draw = scored[0][1]
                match_status = "matched"
                match_method = "best_overlap_same_date"
                match_confidence = "medium"

    if matched_draw is not None:
        enriched["draw_id"] = matched_draw["draw_id"]
        enriched["slot"] = matched_draw["slot"]
        enriched["time"] = matched_draw["time"]
        enriched["numbers"] = [int(n) for n in matched_draw["numbers"]]
        enriched["numbers_sorted"] = [int(n) for n in matched_draw["numbers_sorted"]]
        enriched["extra_numbers"] = [int(n) for n in matched_draw.get("extra_numbers", [])]
        enriched["extra_numbers_sorted"] = [int(n) for n in matched_draw.get("extra_numbers_sorted", [])]
        enriched["draw_source"] = matched_draw.get("source", ROOT_SOURCE_NAME)
        enriched["draw_source_url"] = matched_draw.get("source_url", ROOT_SOURCE_URL)
        enriched["pdf_numbers_match_draw"] = pdf_numbers_sorted == enriched["numbers_sorted"]
        enriched["resolved_from_pdf_numbers"] = not enriched["pdf_numbers_match_draw"]
    else:
        enriched["draw_id"] = None
        enriched["slot"] = None
        enriched["time"] = None
        enriched["numbers"] = [int(n) for n in pdf_numbers]
        enriched["numbers_sorted"] = pdf_numbers_sorted
        enriched["extra_numbers"] = []
        enriched["extra_numbers_sorted"] = []
        enriched["draw_source"] = None
        enriched["draw_source_url"] = None
        enriched["pdf_numbers_match_draw"] = False
        enriched["resolved_from_pdf_numbers"] = False

    enriched["match_status"] = match_status
    enriched["match_method"] = match_method
    enriched["match_confidence"] = match_confidence
    return enriched


def enrich_winners(data_dir: str) -> tuple[dict[str, Any], int]:
    root = ensure_layout(data_dir)
    payload = load_json(winners_file(root), {})
    records = payload.get("records", [])
    draws = load_all_draws(root)
    by_date_numbers, by_date = build_draw_indexes(draws)

    enriched_records = [enrich_record(record, by_date_numbers, by_date) for record in records]
    enrichment_counter = Counter(record["match_method"] for record in enriched_records)
    changed = 0
    if records != enriched_records:
        changed = 1

    new_payload = deepcopy(payload)
    new_payload["updated_at"] = utc_now_iso()
    new_payload["unique_records"] = len(enriched_records)
    new_payload["records"] = enriched_records
    new_payload["enrichment"] = {
        "draw_source": ROOT_SOURCE_NAME,
        "draw_source_url": ROOT_SOURCE_URL,
        "exact_matches": enrichment_counter.get("exact_date_numbers", 0),
        "date_only_matches": enrichment_counter.get("unique_draw_same_date", 0),
        "overlap_matches": enrichment_counter.get("best_overlap_same_date", 0),
        "ambiguous": enrichment_counter.get("multiple_draws_same_date_numbers", 0),
        "unmatched": enrichment_counter.get("none", 0),
    }
    dump_json(winners_file(root), new_payload)
    return new_payload, changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Arricchisce winners.json con draw_id, slot ed extra_numbers")
    parser.add_argument("--data-dir", default=".", help="Root della repo dati")
    args = parser.parse_args()

    root = ensure_layout(args.data_dir)
    payload = load_json(winners_file(root), {})
    for record in payload.get("records", []):
        date.fromisoformat(record["date"])

    new_payload, _ = enrich_winners(args.data_dir)
    enrichment = new_payload.get("enrichment", {})
    print(
        "Winners arricchiti: "
        f"exact={enrichment.get('exact_matches', 0)}, "
        f"date_only={enrichment.get('date_only_matches', 0)}, "
        f"overlap={enrichment.get('overlap_matches', 0)}, "
        f"ambiguous={enrichment.get('ambiguous', 0)}, "
        f"unmatched={enrichment.get('unmatched', 0)}"
    )


if __name__ == "__main__":
    main()
