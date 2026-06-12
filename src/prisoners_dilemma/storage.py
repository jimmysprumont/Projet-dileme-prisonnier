from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from prisoners_dilemma.simulation import TournamentResult


BRONZE_TABLES = ("runs", "players", "matches", "rounds")
SILVER_TABLES = ("silver_rounds", "silver_player_rounds", "silver_player_match_stats")
GOLD_TABLES = (
    "tournament_summary",
    "matchup_matrix",
    "behavioral_drift",
    "forgiveness_index",
    "run_comparison",
)


def write_bronze_parquet(
    result: TournamentResult,
    data_dir: str | Path,
) -> dict[str, Path]:
    base = Path(data_dir) / "bronze" / f"run_id={result.run_id}"
    base.mkdir(parents=True, exist_ok=True)

    tables: dict[str, list[dict[str, Any]]] = {
        "runs": result.runs,
        "players": result.players,
        "matches": result.matches,
        "rounds": result.rounds,
    }
    paths: dict[str, Path] = {}
    for name, rows in tables.items():
        path = base / f"{name}.parquet"
        pd.DataFrame(rows).to_parquet(path, index=False)
        paths[name] = path
    return paths


def bronze_glob(data_dir: str | Path, table_name: str) -> str:
    return str(Path(data_dir) / "bronze" / "run_id=*" / f"{table_name}.parquet")


def export_dbt_tables_to_parquet(
    database_path: str | Path,
    data_dir: str | Path,
    run_id: str,
    silver_tables: list[str] | tuple[str, ...] = SILVER_TABLES,
    gold_tables: list[str] | tuple[str, ...] = GOLD_TABLES,
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    database = Path(database_path)
    base_data_dir = Path(data_dir)

    with duckdb.connect(str(database), read_only=True) as conn:
        for table_name in silver_tables:
            paths[table_name] = _export_table(
                conn=conn,
                table_name=table_name,
                output_path=base_data_dir / "silver" / f"run_id={run_id}" / f"{table_name}.parquet",
                run_id=run_id,
            )
        for table_name in gold_tables:
            paths[table_name] = _export_table(
                conn=conn,
                table_name=table_name,
                output_path=base_data_dir / "gold" / f"run_id={run_id}" / f"{table_name}.parquet",
                run_id=run_id,
            )
    return paths


def validate_gold_parquet_exports(paths: dict[str, Path]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table_name in GOLD_TABLES:
        path = paths.get(table_name)
        if path is None or not path.exists():
            raise FileNotFoundError(f"Missing Gold export for {table_name}")
        row_count = len(pd.read_parquet(path))
        if row_count == 0:
            raise ValueError(f"Gold export is empty: {table_name}")
        counts[table_name] = row_count
    return counts


def _export_table(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    output_path: Path,
    run_id: str,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    conn.execute(
        f"copy (select * from {table_name} where run_id = ?) "
        f"to '{output_path.as_posix()}' (format parquet)",
        [run_id],
    )
    return output_path
