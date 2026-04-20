from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(script_name: str, data_dir: str) -> None:
    scripts_dir = Path(__file__).resolve().parent
    script_path = scripts_dir / script_name
    subprocess.run([sys.executable, str(script_path), "--data-dir", data_dir], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Esegue sync, stats e validazione")
    parser.add_argument("--data-dir", default=".", help="Root della repo dati")
    args = parser.parse_args()

    run("sync_latest.py", args.data_dir)
    run("build_stats.py", args.data_dir)
    run("validate_data.py", args.data_dir)


if __name__ == "__main__":
    main()
