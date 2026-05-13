from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx

from common import ROOT_SOURCE_NAME, ROOT_SOURCE_URL, canonical_number_key

ARCHIVE_API_URL = "https://www.lotto-italia.it/md/estrazioni-e-vincite/ultime-estrazioni-millionDay.json"
ARCHIVE_START_DATE = date(2018, 2, 7)
DEFAULT_BATCH_SIZE = 1000

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Content-Type": "application/json",
    "Referer": ROOT_SOURCE_URL,
}


def _api_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y%m%d")


def _parse_progressivo(value: Any) -> date:
    text = str(value)
    if len(text) != 8 or not text.isdigit():
        raise ValueError(f"progressivo non valido: {value!r}")
    return date(int(text[:4]), int(text[4:6]), int(text[6:8]))


def _numbers(values: Any) -> list[int]:
    if not isinstance(values, list):
        return []
    try:
        return [int(value) for value in values]
    except (TypeError, ValueError):
        return []


def _build_draw(record: dict[str, Any]) -> dict[str, Any] | None:
    numbers = _numbers(record.get("numeriEstratti"))
    if len(numbers) != 5:
        return None

    time_value = str(record.get("orarioEstrazione") or "").strip()
    if time_value not in {"13:00", "20:30"}:
        return None

    extras = _numbers(record.get("numeriEstrattiOvertime"))
    if len(extras) not in {0, 5}:
        return None

    draw_date = _parse_progressivo(record.get("progressivo"))
    date_iso = draw_date.isoformat()
    slot = "midday" if time_value == "13:00" else "evening"
    return {
        "draw_id": f"{date_iso}-{slot}",
        "date": date_iso,
        "slot": slot,
        "time": time_value,
        "numbers": numbers,
        "numbers_sorted": list(canonical_number_key(numbers)),
        "extra_numbers": extras,
        "extra_numbers_sorted": list(canonical_number_key(extras)) if extras else [],
        "source": ROOT_SOURCE_NAME,
        "source_url": ROOT_SOURCE_URL,
    }


def parse_archive_payload(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise ValueError("payload archivio non valido: attesa una lista")

    draws: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in payload:
        if not isinstance(record, dict):
            continue
        draw = _build_draw(record)
        if draw is None or draw["draw_id"] in seen:
            continue
        seen.add(draw["draw_id"])
        draws.append(draw)

    draws.sort(key=lambda item: (item["date"], item["time"]))
    return draws


def fetch_archive_payload(
    *,
    reference_date: date | None = None,
    count: int = 30,
    timeout_seconds: float = 30.0,
) -> list[dict[str, Any]]:
    if count <= 0:
        raise ValueError("count deve essere maggiore di zero")

    body: dict[str, str] = {"numeroEstrazioni": str(count)}
    api_date = _api_date(reference_date)
    if api_date is not None:
        body["data"] = api_date

    response = httpx.post(
        ARCHIVE_API_URL,
        json=body,
        headers=DEFAULT_HEADERS,
        timeout=timeout_seconds,
        follow_redirects=True,
    )
    response.raise_for_status()
    return response.json()


def fetch_recent_draws(
    *,
    reference_date: date | None = None,
    count: int = 30,
    timeout_seconds: float = 30.0,
) -> list[dict[str, Any]]:
    payload = fetch_archive_payload(
        reference_date=reference_date,
        count=count,
        timeout_seconds=timeout_seconds,
    )
    return parse_archive_payload(payload)


def fetch_all_draws(
    *,
    reference_date: date | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    timeout_seconds: float = 30.0,
) -> list[dict[str, Any]]:
    if batch_size <= 0:
        raise ValueError("batch_size deve essere maggiore di zero")

    cursor = reference_date or date.today()
    merged: dict[str, dict[str, Any]] = {}

    while True:
        draws = fetch_recent_draws(reference_date=cursor, count=batch_size, timeout_seconds=timeout_seconds)
        if not draws:
            break

        before = len(merged)
        for draw in draws:
            merged[draw["draw_id"]] = draw

        earliest = min(date.fromisoformat(draw["date"]) for draw in draws)
        if earliest <= ARCHIVE_START_DATE:
            break

        cursor = earliest - timedelta(days=1)
        if len(merged) == before:
            break

    return sorted(merged.values(), key=lambda item: (item["date"], item["time"]))
