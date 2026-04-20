from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
from statistics import mean

from common import canonical_number_key, dump_json, ensure_layout, load_all_draws, utc_now_iso


def top_counter_pairs(counter: Counter, limit: int = 10) -> list[list[int | list[int]]]:
    items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]
    result = []
    for key, count in items:
        if isinstance(key, tuple):
            result.append([list(key), count])
        else:
            result.append([key, count])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Rigenera stats/curiosities.json")
    parser.add_argument("--data-dir", default=".", help="Root della repo dati")
    args = parser.parse_args()

    root = ensure_layout(args.data_dir)
    draws = load_all_draws(root)

    number_counter: Counter[int] = Counter()
    extra_counter: Counter[int] = Counter()
    pair_counter: Counter[tuple[int, int]] = Counter()
    midday_counter: Counter[int] = Counter()
    evening_counter: Counter[int] = Counter()
    overlaps: list[int] = []
    repeated_draws = 0

    previous_key: tuple[int, ...] | None = None
    for draw in draws:
        numbers_key = canonical_number_key(draw["numbers"])
        number_counter.update(numbers_key)
        if draw.get("extra_numbers"):
            extra_counter.update(canonical_number_key(draw["extra_numbers"]))
        for pair in combinations(numbers_key, 2):
            pair_counter[pair] += 1
        if draw["slot"] == "midday":
            midday_counter.update(numbers_key)
        else:
            evening_counter.update(numbers_key)
        if previous_key is not None:
            overlap = len(set(previous_key) & set(numbers_key))
            overlaps.append(overlap)
            if overlap > 0:
                repeated_draws += 1
        previous_key = numbers_key

    hot_numbers = [[n, c] for n, c in sorted(number_counter.items(), key=lambda item: (-item[1], item[0]))[:10]]
    cold_numbers = [[n, c] for n, c in sorted(number_counter.items(), key=lambda item: (item[1], item[0]))[:10]]
    payload = {
        "updated_at": utc_now_iso(),
        "draw_count": len(draws),
        "from_date": draws[0]["date"] if draws else None,
        "to_date": draws[-1]["date"] if draws else None,
        "hot_numbers": hot_numbers,
        "cold_numbers": cold_numbers,
        "hot_pairs": top_counter_pairs(pair_counter),
        "midday_best": top_counter_pairs(midday_counter),
        "evening_best": top_counter_pairs(evening_counter),
        "avg_overlap": round(mean(overlaps), 4) if overlaps else 0.0,
        "repeated_draws": repeated_draws,
        "extra_hot_numbers": top_counter_pairs(extra_counter),
    }

    dump_json(root / "stats" / "curiosities.json", payload)
    print(f"Curiosita aggiornate: {len(draws)} estrazioni analizzate")


if __name__ == "__main__":
    main()
