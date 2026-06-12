from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Choice(str, Enum):
    COOPERATE = "C"
    DEFECT = "D"

    @classmethod
    def from_token(cls, token: str) -> "Choice":
        normalized = token.strip().upper()
        if normalized in {"C", "COOPERATE", "COOPERATION"}:
            return cls.COOPERATE
        if normalized in {"D", "DEFECT", "DEFECTION"}:
            return cls.DEFECT
        raise ValueError(f"Unsupported choice token: {token!r}")


@dataclass(frozen=True)
class PayoffMatrix:
    cc: tuple[int, int]
    cd: tuple[int, int]
    dc: tuple[int, int]
    dd: tuple[int, int]

    @classmethod
    def standard(cls) -> "PayoffMatrix":
        return cls(cc=(3, 3), cd=(0, 5), dc=(5, 0), dd=(1, 1))

    @classmethod
    def from_mapping(cls, mapping: dict[str, list[int] | tuple[int, int]]) -> "PayoffMatrix":
        return cls(
            cc=tuple(mapping["CC"]),  # type: ignore[arg-type]
            cd=tuple(mapping["CD"]),  # type: ignore[arg-type]
            dc=tuple(mapping["DC"]),  # type: ignore[arg-type]
            dd=tuple(mapping["DD"]),  # type: ignore[arg-type]
        )

    def as_dict(self) -> dict[str, tuple[int, int]]:
        return {
            "CC": self.cc,
            "CD": self.cd,
            "DC": self.dc,
            "DD": self.dd,
        }


def score_round(
    player_a_choice: Choice,
    player_b_choice: Choice,
    payoff_matrix: PayoffMatrix,
) -> tuple[int, int]:
    key = f"{player_a_choice.value}{player_b_choice.value}".lower()
    return getattr(payoff_matrix, key)


@dataclass
class RoundObservation:
    round_index: int
    my_choice: Choice
    opponent_choice: Choice
    my_payoff: int
    opponent_payoff: int
    my_cumulative_score: int
    opponent_cumulative_score: int


@dataclass
class PlayerMemory:
    observations: list[RoundObservation] = field(default_factory=list)

    @property
    def last(self) -> RoundObservation | None:
        if not self.observations:
            return None
        return self.observations[-1]

    def opponent_has_defected(self) -> bool:
        return any(obs.opponent_choice is Choice.DEFECT for obs in self.observations)

    def recent_my_choices(self, window: int) -> list[Choice]:
        return [obs.my_choice for obs in self.observations[-window:]]

    def recent_opponent_choices(self, window: int) -> list[Choice]:
        return [obs.opponent_choice for obs in self.observations[-window:]]
