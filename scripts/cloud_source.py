from __future__ import annotations

import re
from datetime import date
from typing import Any

import httpx
from bs4 import BeautifulSoup

from common import ROOT_SOURCE_NAME, ROOT_SOURCE_URL, canonical_number_key

MONTHS = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}

DRAW_RE = re.compile(
    r"(?P<weekday>Lunedì|Lunedì|Martedì|Mercoledì|Giovedì|Venerdì|Sabato|Domenica)\s+"
    r"(?P<day>\d{1,2})\s+"
    r"(?P<month>Gennaio|Febbraio|Marzo|Aprile|Maggio|Giugno|Luglio|Agosto|Settembre|Ottobre|Novembre|Dicembre)\s+"
    r"(?P<year>\d{4})\s+ore\s+"
    r"(?P<time>13:00|20:30)\s+"
    r"(?P<numbers>(?:\d{1,2}\s+){4}\d{1,2})"
    r"(?:\s+(?P<extras>(?:\d{1,2}\s+){4}\d{1,2}))?"
)


def fetch_archive_html(timeout_seconds: float = 30.0) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/135.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
        "Referer": "https://www.millionday.cloud/",
    }
    response = httpx.get(ROOT_SOURCE_URL, headers=headers, timeout=timeout_seconds, follow_redirects=True)
    response.raise_for_status()
    return response.text


def _slice_archive_text(text: str) -> str:
    start_marker = "Archivio Estrazioni Million Day"
    end_marker_candidates = ["Back to top", "Cookie Policy", "© 2018"]

    start = text.find(start_marker)
    if start == -1:
        return text
    sliced = text[start:]
    for marker in end_marker_candidates:
        idx = sliced.find(marker)
        if idx != -1:
            sliced = sliced[:idx]
            break
    return sliced


def _parse_number_block(block: str | None) -> list[int]:
    if not block:
        return []
    return [int(part) for part in block.split()]


def _build_draw(day: int, month_name: str, year: int, time_value: str, numbers: list[int], extras: list[int]) -> dict[str, Any]:
    month = MONTHS[month_name.lower()]
    draw_date = date(year, month, day)
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


def parse_archive_html(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    text = text.replace("\ufeff", "")
    text = _slice_archive_text(text)

    draws: list[dict[str, Any]] = []
    seen: set[str] = set()

    for match in DRAW_RE.finditer(text):
        day = int(match.group("day"))
        month_name = match.group("month")
        year = int(match.group("year"))
        time_value = match.group("time")
        numbers = _parse_number_block(match.group("numbers"))
        extras = _parse_number_block(match.group("extras"))
        draw = _build_draw(day, month_name, year, time_value, numbers, extras)
        if draw["draw_id"] not in seen:
            seen.add(draw["draw_id"])
            draws.append(draw)

    draws.sort(key=lambda item: (item["date"], item["time"]))
    return draws
