from __future__ import annotations

import argparse
import sys
from datetime import date

from official_source import fetch_all_draws, fetch_recent_draws
from common import ensure_layout, load_all_draws, refresh_index_and_latest, upsert_draws


def recommended_fetch_count(existing: list[dict], lookback_draws: int) -> int:
    count = max(lookback_draws, 1)
    if existing:
        latest = existing[-1]
        gap_days = max(0, (date.today() - date.fromisoformat(latest["date"])).days)
        count = max(count, gap_days * 2 + 8)
    return count + 4


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggiorna l'archivio leggendo l'API ufficiale Lotto Italia")
    parser.add_argument("--data-dir", default=".", help="Root della repo dati")
    parser.add_argument(
        "--lookback-draws",
        type=int,
        default=20,
        help="Numero di estrazioni più recenti da considerare per il sync",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout HTTP in secondi")
    args = parser.parse_args()

    root = ensure_layout(args.data_dir)
    existing = load_all_draws(root)
    if args.lookback_draws > 0:
        fetch_count = recommended_fetch_count(existing, args.lookback_draws)
        incoming = fetch_recent_draws(count=fetch_count, timeout_seconds=args.timeout)
    else:
        incoming = fetch_all_draws(timeout_seconds=args.timeout)

    merged, changes = upsert_draws(existing, incoming)
    refresh_index_and_latest(root, merged)
    print(f"Sync completato. Trovate {len(incoming)} estrazioni, modifiche applicate: {changes}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"Errore sync: {exc}", file=sys.stderr)
        raise
