from __future__ import annotations

from pathlib import Path
from typing import Any

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
