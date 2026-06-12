from prisoners_dilemma.config import (
    ProjectConfig,
    RunConfig,
    SimulationConfig,
    StrategiesConfig,
    VLLMConfig,
)
from prisoners_dilemma.domain import PayoffMatrix
from prisoners_dilemma.simulation import simulate_tournament


def tiny_config() -> ProjectConfig:
    return ProjectConfig(
        run=RunConfig(seed=7, run_id="test-run", data_dir="data"),
        simulation=SimulationConfig(
            coded_rounds=2,
            ai_rounds=1,
            round_bucket_size=1,
            include_ai=False,
            request_timeout_seconds=1,
            history_window=2,
            payoff_matrix=PayoffMatrix.standard(),
        ),
        strategies=StrategiesConfig(
            coded=["always_cooperate", "always_defect"],
            ai_profiles=[],
        ),
        vllm=VLLMConfig(enabled=False, base_url="http://127.0.0.1:8000/v1", model="none"),
    )


def test_simulate_tournament_generates_bronze_tables() -> None:
    result = simulate_tournament(tiny_config())

    assert len(result.runs) == 1
    assert len(result.players) == 2
    assert len(result.matches) == 4
    assert len(result.rounds) == 8


def test_simulate_tournament_records_scores_and_cumulative_scores() -> None:
    result = simulate_tournament(tiny_config())
    rounds = [
        row
        for row in result.rounds
        if row["player_a_id"] == "coded:always_cooperate"
        and row["player_b_id"] == "coded:always_defect"
    ]

    assert [row["player_a_choice"] for row in rounds] == ["C", "C"]
    assert [row["player_b_choice"] for row in rounds] == ["D", "D"]
    assert [row["player_a_payoff"] for row in rounds] == [0, 0]
    assert [row["player_b_payoff"] for row in rounds] == [5, 5]
    assert rounds[-1]["player_a_cumulative_score"] == 0
    assert rounds[-1]["player_b_cumulative_score"] == 10
