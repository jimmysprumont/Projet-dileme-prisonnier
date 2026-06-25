from pathlib import Path

import yaml

from prisoners_dilemma.config import load_config, parse_config


def minimal_config(ai_profiles: list[dict[str, str]]) -> dict:
    return {
        "run": {"seed": 42, "run_id": None, "data_dir": "data"},
        "simulation": {
            "coded_rounds": 1,
            "ai_rounds": 1,
            "round_bucket_size": 1,
            "include_ai": True,
            "request_timeout_seconds": 1,
            "history_window": 1,
            "payoff_matrix": {
                "CC": [3, 3],
                "CD": [0, 5],
                "DC": [5, 0],
                "DD": [1, 1],
            },
        },
        "strategies": {
            "coded": ["always_cooperate"],
            "ai_profiles": ai_profiles,
        },
        "vllm": {
            "enabled": True,
            "base_url": "http://127.0.0.1:8000/v1",
            "model": "test-model",
        },
    }


def test_parse_config_keeps_inline_ai_prompts() -> None:
    config = parse_config(
        minimal_config(
            [
                {
                    "name": "inline_ai",
                    "prompt": "Choose C when trust is useful.",
                }
            ]
        )
    )

    assert config.strategies.ai_profiles[0].name == "inline_ai"
    assert config.strategies.ai_profiles[0].prompt == "Choose C when trust is useful."


def test_load_config_reads_prompt_file_from_project_root(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    agents_dir = tmp_path / "agents"
    config_dir.mkdir()
    agents_dir.mkdir()
    (agents_dir / "empathic_ai.md").write_text("Prefer cooperation.\n", encoding="utf-8")
    config_path = config_dir / "default.yaml"
    config_path.write_text(
        yaml.safe_dump(
            minimal_config(
                [
                    {
                        "name": "empathic_ai",
                        "prompt_file": "agents/empathic_ai.md",
                    }
                ]
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.strategies.ai_profiles[0].prompt == "Prefer cooperation."
