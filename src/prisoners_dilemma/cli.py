from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from prisoners_dilemma.config import load_config
from prisoners_dilemma.simulation import simulate_tournament
from prisoners_dilemma.storage import write_bronze_parquet


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Prisoners dilemma ETL pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate_parser = subparsers.add_parser("simulate", help="Generate Bronze Parquet data.")
    simulate_parser.add_argument("--config", default="configs/default.yaml")

    run_parser = subparsers.add_parser("run", help="Run simulation, dbt, and exports.")
    run_parser.add_argument("--config", default="configs/default.yaml")

    subparsers.add_parser("clean-data", help="Remove generated local data.")

    args = parser.parse_args(argv)

    if args.command == "simulate":
        _simulate(args.config)
    elif args.command == "run":
        _simulate(args.config)
        _dbt_build()
    elif args.command == "clean-data":
        shutil.rmtree("data", ignore_errors=True)


def _simulate(config_path: str) -> None:
    config = load_config(config_path)
    result = simulate_tournament(config)
    paths = write_bronze_parquet(result, data_dir=config.run.data_dir)
    for table_name, path in paths.items():
        print(f"wrote {table_name}: {path}")


def _dbt_build() -> None:
    project_dir = Path("dbt_prisoners")
    if not project_dir.exists():
        print("dbt_prisoners does not exist yet; skipping dbt build")
        return
    subprocess.run(
        [
            "dbt",
            "build",
            "--project-dir",
            "dbt_prisoners",
            "--profiles-dir",
            "dbt_prisoners",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
