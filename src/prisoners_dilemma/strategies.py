from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Protocol

from prisoners_dilemma.domain import Choice, PlayerMemory


class Strategy(Protocol):
    name: str

    def choose(self, memory: PlayerMemory) -> Choice:
        ...


@dataclass
class AlwaysCooperate:
    name: str = "always_cooperate"

    def choose(self, memory: PlayerMemory) -> Choice:
        return Choice.COOPERATE


@dataclass
class AlwaysDefect:
    name: str = "always_defect"

    def choose(self, memory: PlayerMemory) -> Choice:
        return Choice.DEFECT


@dataclass
class TitForTat:
    name: str = "tit_for_tat"

    def choose(self, memory: PlayerMemory) -> Choice:
        if memory.last is None:
            return Choice.COOPERATE
        return memory.last.opponent_choice


@dataclass
class GrimTrigger:
    name: str = "grim_trigger"

    def choose(self, memory: PlayerMemory) -> Choice:
        if memory.opponent_has_defected():
            return Choice.DEFECT
        return Choice.COOPERATE


@dataclass
class RandomStrategy:
    rng: random.Random = field(default_factory=random.Random)
    name: str = "random"

    def choose(self, memory: PlayerMemory) -> Choice:
        return self.rng.choice([Choice.COOPERATE, Choice.DEFECT])


@dataclass
class GenerousTitForTat:
    rng: random.Random = field(default_factory=random.Random)
    forgiveness_probability: float = 0.1
    name: str = "generous_tit_for_tat"

    def choose(self, memory: PlayerMemory) -> Choice:
        if memory.last is None:
            return Choice.COOPERATE
        if memory.last.opponent_choice is Choice.COOPERATE:
            return Choice.COOPERATE
        if self.rng.random() < self.forgiveness_probability:
            return Choice.COOPERATE
        return Choice.DEFECT


def build_strategy(name: str, rng: random.Random | None = None) -> Strategy:
    strategy_rng = rng or random.Random()
    if name == "always_cooperate":
        return AlwaysCooperate()
    if name == "always_defect":
        return AlwaysDefect()
    if name == "tit_for_tat":
        return TitForTat()
    if name == "random":
        return RandomStrategy(rng=strategy_rng)
    if name == "grim_trigger":
        return GrimTrigger()
    if name == "generous_tit_for_tat":
        return GenerousTitForTat(rng=strategy_rng)
    raise ValueError(f"Unknown strategy: {name}")
