from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT_SOURCE_NAME = "millionday.cloud"
ROOT_SOURCE_URL = "https://www.millionday.cloud/archivio-estrazioni.php"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_layout(data_dir: str | Path) -> Path:
    root = Path(data_dir)
    (root / "years").mkdir(parents=True, exist_ok=True)
    (root / "stats").mkdir(parents=True, exist_ok=True)
    return root


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def draw_sort_key(draw: dict[str, Any]) -> tuple[str, str]:
    return draw["date"], draw["time"]


def canonical_number_key(numbers: Iterable[int]) -> tuple[int, ...]:
    return tuple(sorted(int(n) for n in numbers))


def year_file(root: Path, year: int) -> Path:
    return root / "years" / f"{year}.json"


def winners_file(root: Path) -> Path:
    return root / "winners.json"


def load_all_draws(root: Path) -> list[dict[str, Any]]:
    index = load_json(root / "index.json", {})
    years = index.get("years", [])
    draws: list[dict[str, Any]] = []
    for year in sorted(years):
        payload = load_json(year_file(root, int(year)), {"year": int(year), "draws": []})
        draws.extend(payload.get("draws", []))
    draws.sort(key=draw_sort_key)
    return draws


def group_draws_by_year(draws: Iterable[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for draw in draws:
        grouped[int(draw["date"][:4])].append(draw)
    for year in grouped:
        grouped[year].sort(key=draw_sort_key)
    return dict(grouped)


def write_grouped_draws(root: Path, grouped: dict[int, list[dict[str, Any]]]) -> None:
    years_dir = root / "years"
    years_dir.mkdir(parents=True, exist_ok=True)

    existing = {int(p.stem) for p in years_dir.glob("*.json") if p.stem.isdigit()}
    incoming = set(grouped.keys())

    for obsolete in existing - incoming:
        year_file(root, obsolete).unlink(missing_ok=True)

    for year, draws in grouped.items():
        dump_json(
            year_file(root, year),
            {
                "year": year,
                "source": ROOT_SOURCE_NAME,
                "source_url": ROOT_SOURCE_URL,
                "draw_count": len(draws),
                "draws": draws,
            },
        )


def refresh_index_and_latest(root: Path, draws: list[dict[str, Any]]) -> None:
    updated_at = utc_now_iso()
    grouped = group_draws_by_year(draws)
    write_grouped_draws(root, grouped)

    years = sorted(grouped.keys())
    latest = max(draws, key=draw_sort_key) if draws else None

    dump_json(
        root / "index.json",
        {
            "updated_at": updated_at,
            "years": years,
            "latest_year": years[-1] if years else None,
            "archive_start_date": "2018-02-07",
            "total_draws": len(draws),
            "latest_draw_id": latest["draw_id"] if latest else None,
            "source": ROOT_SOURCE_NAME,
            "source_url": ROOT_SOURCE_URL,
            "is_demo": False,
        },
    )

    dump_json(
        root / "latest.json",
        {
            "updated_at": updated_at,
            "source_name": ROOT_SOURCE_NAME,
            "source_url": ROOT_SOURCE_URL,
            "is_demo": False,
            "draw": latest,
        },
    )


def upsert_draws(existing: Iterable[dict[str, Any]], incoming: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    merged: dict[str, dict[str, Any]] = {draw["draw_id"]: draw for draw in existing}
    changes = 0
    for draw in incoming:
        draw_id = draw["draw_id"]
        old = merged.get(draw_id)
        if old != draw:
            merged[draw_id] = draw
            changes += 1
    ordered = sorted(merged.values(), key=draw_sort_key)
    return ordered, changes
