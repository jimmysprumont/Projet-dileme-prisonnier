import pandas as pd
import duckdb

from tests.test_simulation import tiny_config

from prisoners_dilemma.simulation import simulate_tournament
from prisoners_dilemma.storage import export_dbt_tables_to_parquet, write_bronze_parquet


def test_write_bronze_parquet_creates_expected_files(tmp_path) -> None:
    config = tiny_config()
    config.run.data_dir = str(tmp_path)
    result = simulate_tournament(config)

    paths = write_bronze_parquet(result, data_dir=tmp_path)

    assert paths["runs"].name == "runs.parquet"
    assert paths["players"].name == "players.parquet"
    assert paths["matches"].name == "matches.parquet"
    assert paths["rounds"].name == "rounds.parquet"
    assert all(path.exists() for path in paths.values())

    rounds = pd.read_parquet(paths["rounds"])
    assert len(rounds) == 8
    assert set(rounds["player_a_choice"].unique()) == {"C", "D"}


def test_export_dbt_tables_to_parquet_writes_silver_and_gold(tmp_path) -> None:
    database_path = tmp_path / "warehouse.duckdb"
    with duckdb.connect(database_path) as conn:
        conn.execute("create table silver_rounds as select 'run-1' as run_id, 1 as value")
        conn.execute(
            "create table tournament_summary as "
            "select 'run-1' as run_id, 'tit_for_tat' as strategy_name, 1.0 as cooperation_rate"
        )

    paths = export_dbt_tables_to_parquet(
        database_path=database_path,
        data_dir=tmp_path,
        run_id="run-1",
        silver_tables=["silver_rounds"],
        gold_tables=["tournament_summary"],
    )

    assert paths["silver_rounds"].exists()
    assert paths["tournament_summary"].exists()
    assert pd.read_parquet(paths["silver_rounds"]).iloc[0]["run_id"] == "run-1"
    assert pd.read_parquet(paths["tournament_summary"]).iloc[0]["strategy_name"] == "tit_for_tat"
