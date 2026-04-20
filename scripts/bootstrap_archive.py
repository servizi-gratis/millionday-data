from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cloud_source import fetch_archive_html, parse_archive_html
from common import ensure_layout, load_all_draws, refresh_index_and_latest, upsert_draws


def main() -> None:
    parser = argparse.ArgumentParser(description="Costruisce l'archivio completo da millionday.cloud")
    parser.add_argument("--data-dir", default=".", help="Root della repo dati")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout HTTP in secondi")
    args = parser.parse_args()

    root = ensure_layout(args.data_dir)
    existing = load_all_draws(root)
    html = fetch_archive_html(timeout_seconds=args.timeout)
    incoming = parse_archive_html(html)

    merged, changes = upsert_draws(existing, incoming)
    refresh_index_and_latest(root, merged)
    print(f"Bootstrap completato. Trovate {len(incoming)} estrazioni, modifiche applicate: {changes}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"Errore bootstrap: {exc}", file=sys.stderr)
        raise
