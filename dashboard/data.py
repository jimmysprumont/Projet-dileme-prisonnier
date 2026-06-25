from __future__ import annotations

from pathlib import Path

import pandas as pd


GOLD_TABLES = (
    "tournament_summary",
    "matchup_matrix",
    "behavioral_drift",
    "forgiveness_index",
    "run_comparison",
)


def available_run_ids(data_dir: str | Path = "data") -> list[str]:
    gold_dir = Path(data_dir) / "gold"
    if not gold_dir.exists():
        return []
    return sorted(
        path.name.split("=", 1)[1]
        for path in gold_dir.glob("run_id=*")
        if path.is_dir() and "=" in path.name
    )


def load_gold_table(data_dir: str | Path, table_name: str) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for run_id in available_run_ids(data_dir):
        path = Path(data_dir) / "gold" / f"run_id={run_id}" / f"{table_name}.parquet"
        if path.exists():
            frames.append(pd.read_parquet(path))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def filter_by_runs_and_strategies(
    frame: pd.DataFrame,
    run_ids: list[str],
    strategies: list[str] | None = None,
) -> pd.DataFrame:
    if frame.empty:
        return frame
    filtered = frame
    if "run_id" in filtered.columns and run_ids:
        filtered = filtered[filtered["run_id"].isin(run_ids)]
    if strategies and "strategy_name" in filtered.columns:
        filtered = filtered[filtered["strategy_name"].isin(strategies)]
    if strategies and {"strategy_a", "strategy_b"}.issubset(filtered.columns):
        filtered = filtered[
            filtered["strategy_a"].isin(strategies) & filtered["strategy_b"].isin(strategies)
        ]
    return filtered.reset_index(drop=True)
