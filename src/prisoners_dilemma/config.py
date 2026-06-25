from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from prisoners_dilemma.domain import PayoffMatrix


@dataclass
class RunConfig:
    seed: int
    run_id: str | None
    data_dir: str

    def resolved_run_id(self) -> str:
        if self.run_id:
            return self.run_id
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"run_{timestamp}"


@dataclass
class SimulationConfig:
    coded_rounds: int
    ai_rounds: int
    round_bucket_size: int
    include_ai: bool
    request_timeout_seconds: int
    history_window: int
    payoff_matrix: PayoffMatrix


@dataclass
class AIProfileConfig:
    name: str
    prompt: str


@dataclass
class StrategiesConfig:
    coded: list[str]
    ai_profiles: list[AIProfileConfig]


@dataclass
class VLLMConfig:
    enabled: bool
    base_url: str
    model: str


@dataclass
class ProjectConfig:
    run: RunConfig
    simulation: SimulationConfig
    strategies: StrategiesConfig
    vllm: VLLMConfig


def load_config(path: str | Path) -> ProjectConfig:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return parse_config(raw, base_dir=config_path.parent)


def parse_config(raw: dict[str, Any], base_dir: Path | None = None) -> ProjectConfig:
    run = raw["run"]
    simulation = raw["simulation"]
    strategies = raw["strategies"]
    vllm = raw["vllm"]

    return ProjectConfig(
        run=RunConfig(
            seed=int(run["seed"]),
            run_id=run.get("run_id"),
            data_dir=str(run["data_dir"]),
        ),
        simulation=SimulationConfig(
            coded_rounds=int(simulation["coded_rounds"]),
            ai_rounds=int(simulation["ai_rounds"]),
            round_bucket_size=int(simulation["round_bucket_size"]),
            include_ai=bool(simulation["include_ai"]),
            request_timeout_seconds=int(simulation["request_timeout_seconds"]),
            history_window=int(simulation["history_window"]),
            payoff_matrix=PayoffMatrix.from_mapping(simulation["payoff_matrix"]),
        ),
        strategies=StrategiesConfig(
            coded=list(strategies["coded"]),
            ai_profiles=[
                AIProfileConfig(name=str(item["name"]), prompt=_read_ai_prompt(item, base_dir))
                for item in strategies.get("ai_profiles", [])
            ],
        ),
        vllm=VLLMConfig(
            enabled=bool(vllm["enabled"]),
            base_url=str(vllm["base_url"]),
            model=str(vllm["model"]),
        ),
    )


def _read_ai_prompt(item: dict[str, Any], base_dir: Path | None) -> str:
    if "prompt_file" not in item:
        return str(item["prompt"])

    raw_path = Path(str(item["prompt_file"]))
    candidates = [raw_path] if raw_path.is_absolute() else []

    if base_dir is not None and not raw_path.is_absolute():
        candidates.extend(
            [
                base_dir / raw_path,
                base_dir.parent / raw_path,
            ]
        )

    if not raw_path.is_absolute():
        candidates.append(raw_path)

    for prompt_path in candidates:
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8").strip()

    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        f"Prompt file not found for AI profile {item['name']!r}: {raw_path}. "
        f"Searched: {searched}"
    )
