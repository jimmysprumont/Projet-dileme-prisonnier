from pathlib import Path

import pandas as pd

from dashboard.data import available_run_ids, filter_by_runs_and_strategies, load_gold_table


def write_table(base: Path, run_id: str, table: str, rows: list[dict]) -> None:
    path = base / "gold" / f"run_id={run_id}" / f"{table}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)


def test_available_run_ids_discovers_gold_partitions(tmp_path: Path) -> None:
    write_table(tmp_path, "run_b", "tournament_summary", [{"run_id": "run_b"}])
    write_table(tmp_path, "run_a", "tournament_summary", [{"run_id": "run_a"}])

    assert available_run_ids(tmp_path) == ["run_a", "run_b"]


def test_load_gold_table_reads_rows_across_runs(tmp_path: Path) -> None:
    write_table(
        tmp_path,
        "run_a",
        "tournament_summary",
        [{"run_id": "run_a", "strategy_name": "tit_for_tat"}],
    )
    write_table(
        tmp_path,
        "run_b",
        "tournament_summary",
        [{"run_id": "run_b", "strategy_name": "grim_trigger"}],
    )

    result = load_gold_table(tmp_path, "tournament_summary")

    assert set(result["run_id"]) == {"run_a", "run_b"}
    assert set(result["strategy_name"]) == {"tit_for_tat", "grim_trigger"}


def test_load_gold_table_returns_empty_dataframe_when_missing(tmp_path: Path) -> None:
    result = load_gold_table(tmp_path, "missing")

    assert result.empty


def test_filter_by_runs_and_strategies_filters_optional_columns() -> None:
    frame = pd.DataFrame(
        [
            {"run_id": "run_a", "strategy_name": "tit_for_tat", "value": 1},
            {"run_id": "run_a", "strategy_name": "grim_trigger", "value": 2},
            {"run_id": "run_b", "strategy_name": "tit_for_tat", "value": 3},
        ]
    )

    result = filter_by_runs_and_strategies(frame, ["run_a"], ["tit_for_tat"])

    assert result.to_dict("records") == [
        {"run_id": "run_a", "strategy_name": "tit_for_tat", "value": 1}
    ]


def test_filter_by_runs_and_strategies_filters_matchup_axes() -> None:
    frame = pd.DataFrame(
        [
            {"run_id": "run_a", "strategy_a": "tit_for_tat", "strategy_b": "grim_trigger"},
            {"run_id": "run_a", "strategy_a": "tit_for_tat", "strategy_b": "always_defect"},
            {"run_id": "run_a", "strategy_a": "random", "strategy_b": "grim_trigger"},
        ]
    )

    result = filter_by_runs_and_strategies(frame, ["run_a"], ["tit_for_tat", "grim_trigger"])

    assert result.to_dict("records") == [
        {"run_id": "run_a", "strategy_a": "tit_for_tat", "strategy_b": "grim_trigger"}
    ]
