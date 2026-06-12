from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from prisoners_dilemma.config import AIProfileConfig, ProjectConfig
from prisoners_dilemma.domain import Choice, PlayerMemory, RoundObservation, score_round
from prisoners_dilemma.strategies import Strategy, build_strategy
from prisoners_dilemma.vllm_client import AIDecision, VLLMClient, fallback_decision


@dataclass
class SimulatedPlayer:
    player_id: str
    strategy_name: str
    strategy_type: str
    profile_prompt: str | None
    strategy: Strategy | None = None
    ai_profile: AIProfileConfig | None = None


@dataclass
class TournamentResult:
    run_id: str
    runs: list[dict[str, Any]]
    players: list[dict[str, Any]]
    matches: list[dict[str, Any]]
    rounds: list[dict[str, Any]]


def simulate_tournament(
    config: ProjectConfig,
    vllm_client: VLLMClient | None = None,
) -> TournamentResult:
    run_id = config.run.resolved_run_id()
    players = _build_players(config)
    rows_players = [
        {
            "run_id": run_id,
            "player_id": player.player_id,
            "strategy_name": player.strategy_name,
            "strategy_type": player.strategy_type,
            "profile_prompt": player.profile_prompt,
        }
        for player in players
    ]

    client = vllm_client
    if client is None and config.simulation.include_ai and config.vllm.enabled:
        client = VLLMClient(
            base_url=config.vllm.base_url,
            model=config.vllm.model,
            timeout_seconds=config.simulation.request_timeout_seconds,
            history_window=config.simulation.history_window,
        )

    matches: list[dict[str, Any]] = []
    rounds: list[dict[str, Any]] = []
    match_counter = 0

    for player_a in players:
        for player_b in players:
            match_counter += 1
            match_id = f"{run_id}_match_{match_counter:04d}"
            includes_ai = "ai" in {player_a.strategy_type, player_b.strategy_type}
            n_rounds = config.simulation.ai_rounds if includes_ai else config.simulation.coded_rounds
            match_type = "ai" if includes_ai else "coded"
            matches.append(
                {
                    "run_id": run_id,
                    "match_id": match_id,
                    "player_a_id": player_a.player_id,
                    "player_b_id": player_b.player_id,
                    "n_rounds": n_rounds,
                    "match_type": match_type,
                }
            )
            rounds.extend(
                _simulate_match(
                    run_id=run_id,
                    match_id=match_id,
                    player_a=player_a,
                    player_b=player_b,
                    n_rounds=n_rounds,
                    config=config,
                    vllm_client=client,
                )
            )

    runs = [
        {
            "run_id": run_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "seed": config.run.seed,
            "payoff_matrix": json.dumps(config.simulation.payoff_matrix.as_dict(), sort_keys=True),
            "n_rounds_coded": config.simulation.coded_rounds,
            "n_rounds_ai": config.simulation.ai_rounds,
            "vllm_model": config.vllm.model if config.vllm.enabled else None,
            "config_hash": _config_hash(config),
        }
    ]

    return TournamentResult(
        run_id=run_id,
        runs=runs,
        players=rows_players,
        matches=matches,
        rounds=rounds,
    )


def _build_players(config: ProjectConfig) -> list[SimulatedPlayer]:
    rng = random.Random(config.run.seed)
    players: list[SimulatedPlayer] = []
    for strategy_name in config.strategies.coded:
        player_rng = random.Random(rng.randint(0, 1_000_000_000))
        players.append(
            SimulatedPlayer(
                player_id=f"coded:{strategy_name}",
                strategy_name=strategy_name,
                strategy_type="coded",
                profile_prompt=None,
                strategy=build_strategy(strategy_name, rng=player_rng),
            )
        )

    if config.simulation.include_ai:
        for profile in config.strategies.ai_profiles:
            players.append(
                SimulatedPlayer(
                    player_id=f"ai:{profile.name}",
                    strategy_name=profile.name,
                    strategy_type="ai",
                    profile_prompt=profile.prompt,
                    ai_profile=profile,
                )
            )
    return players


def _simulate_match(
    run_id: str,
    match_id: str,
    player_a: SimulatedPlayer,
    player_b: SimulatedPlayer,
    n_rounds: int,
    config: ProjectConfig,
    vllm_client: VLLMClient | None,
) -> list[dict[str, Any]]:
    memory_a = PlayerMemory()
    memory_b = PlayerMemory()
    cumulative_a = 0
    cumulative_b = 0
    rows: list[dict[str, Any]] = []

    for round_index in range(1, n_rounds + 1):
        decision_a = _choose(player_a, memory_a, vllm_client)
        decision_b = _choose(player_b, memory_b, vllm_client)
        payoff_a, payoff_b = score_round(
            decision_a.choice,
            decision_b.choice,
            config.simulation.payoff_matrix,
        )
        cumulative_a += payoff_a
        cumulative_b += payoff_b

        row = {
            "run_id": run_id,
            "match_id": match_id,
            "round_index": round_index,
            "player_a_id": player_a.player_id,
            "player_b_id": player_b.player_id,
            "player_a_choice": decision_a.choice.value,
            "player_b_choice": decision_b.choice.value,
            "player_a_payoff": payoff_a,
            "player_b_payoff": payoff_b,
            "player_a_cumulative_score": cumulative_a,
            "player_b_cumulative_score": cumulative_b,
            "player_a_reasoning": decision_a.reasoning,
            "player_b_reasoning": decision_b.reasoning,
            "player_a_decision_source": decision_a.source,
            "player_b_decision_source": decision_b.source,
        }
        rows.append(row)

        memory_a.observations.append(
            RoundObservation(
                round_index=round_index,
                my_choice=decision_a.choice,
                opponent_choice=decision_b.choice,
                my_payoff=payoff_a,
                opponent_payoff=payoff_b,
                my_cumulative_score=cumulative_a,
                opponent_cumulative_score=cumulative_b,
            )
        )
        memory_b.observations.append(
            RoundObservation(
                round_index=round_index,
                my_choice=decision_b.choice,
                opponent_choice=decision_a.choice,
                my_payoff=payoff_b,
                opponent_payoff=payoff_a,
                my_cumulative_score=cumulative_b,
                opponent_cumulative_score=cumulative_a,
            )
        )
    return rows


def _choose(
    player: SimulatedPlayer,
    memory: PlayerMemory,
    vllm_client: VLLMClient | None,
) -> AIDecision:
    if player.strategy_type == "coded":
        if player.strategy is None:
            raise ValueError(f"Coded player has no strategy: {player.player_id}")
        choice = player.strategy.choose(memory)
        return AIDecision(choice=choice, reasoning=f"Coded strategy {player.strategy_name}.", source="coded")

    if player.ai_profile is None:
        raise ValueError(f"AI player has no profile: {player.player_id}")
    if vllm_client is None:
        return fallback_decision(memory)
    return vllm_client.decide(
        profile_name=player.ai_profile.name,
        profile_prompt=player.ai_profile.prompt,
        memory=memory,
    )


def _config_hash(config: ProjectConfig) -> str:
    payload = {
        "seed": config.run.seed,
        "coded_rounds": config.simulation.coded_rounds,
        "ai_rounds": config.simulation.ai_rounds,
        "payoff_matrix": config.simulation.payoff_matrix.as_dict(),
        "coded": config.strategies.coded,
        "ai_profiles": [profile.__dict__ for profile in config.strategies.ai_profiles],
        "vllm_model": config.vllm.model,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]
