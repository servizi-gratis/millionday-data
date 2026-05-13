from __future__ import annotations

import argparse
import sys

from official_source import DEFAULT_BATCH_SIZE, fetch_all_draws
from common import ensure_layout, load_all_draws, refresh_index_and_latest, upsert_draws


def main() -> None:
    parser = argparse.ArgumentParser(description="Costruisce l'archivio completo dall'API ufficiale Lotto Italia")
    parser.add_argument("--data-dir", default=".", help="Root della repo dati")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout HTTP in secondi")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Numero di estrazioni richieste per ogni finestra API",
    )
    args = parser.parse_args()

    root = ensure_layout(args.data_dir)
    existing = load_all_draws(root)
    incoming = fetch_all_draws(batch_size=args.batch_size, timeout_seconds=args.timeout)

    merged, changes = upsert_draws(existing, incoming)
    refresh_index_and_latest(root, merged)
    print(f"Bootstrap completato. Trovate {len(incoming)} estrazioni, modifiche applicate: {changes}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"Errore bootstrap: {exc}", file=sys.stderr)
        raise
