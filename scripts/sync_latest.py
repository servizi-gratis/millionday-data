from __future__ import annotations

import argparse
import sys

from cloud_source import fetch_archive_html, parse_archive_html
from common import ensure_layout, load_all_draws, refresh_index_and_latest, upsert_draws


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggiorna l'archivio leggendo l'ultima pagina archivio")
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
    html = fetch_archive_html(timeout_seconds=args.timeout)
    parsed = parse_archive_html(html)
    if args.lookback_draws > 0:
        incoming = parsed[-args.lookback_draws :]
    else:
        incoming = parsed

    merged, changes = upsert_draws(existing, incoming)
    refresh_index_and_latest(root, merged)
    print(f"Sync completato. Trovate {len(incoming)} estrazioni recenti, modifiche applicate: {changes}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"Errore sync: {exc}", file=sys.stderr)
        raise
