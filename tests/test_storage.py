import pandas as pd

from tests.test_simulation import tiny_config

from prisoners_dilemma.simulation import simulate_tournament
from prisoners_dilemma.storage import write_bronze_parquet


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
