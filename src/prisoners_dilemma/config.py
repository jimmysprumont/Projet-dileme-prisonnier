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
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return parse_config(raw)


def parse_config(raw: dict[str, Any]) -> ProjectConfig:
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
                AIProfileConfig(name=str(item["name"]), prompt=str(item["prompt"]))
                for item in strategies.get("ai_profiles", [])
            ],
        ),
        vllm=VLLMConfig(
            enabled=bool(vllm["enabled"]),
            base_url=str(vllm["base_url"]),
            model=str(vllm["model"]),
        ),
    )
