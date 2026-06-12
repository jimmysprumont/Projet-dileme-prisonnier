import random

from prisoners_dilemma.domain import Choice, PlayerMemory, RoundObservation
from prisoners_dilemma.strategies import (
    AlwaysCooperate,
    AlwaysDefect,
    GenerousTitForTat,
    GrimTrigger,
    RandomStrategy,
    TitForTat,
)


def observation(my_choice: Choice, opponent_choice: Choice) -> RoundObservation:
    return RoundObservation(
        round_index=1,
        my_choice=my_choice,
        opponent_choice=opponent_choice,
        my_payoff=0,
        opponent_payoff=0,
        my_cumulative_score=0,
        opponent_cumulative_score=0,
    )


def test_always_cooperate_returns_cooperation() -> None:
    assert AlwaysCooperate().choose(PlayerMemory()) is Choice.COOPERATE


def test_always_defect_returns_defection() -> None:
    assert AlwaysDefect().choose(PlayerMemory()) is Choice.DEFECT


def test_tit_for_tat_starts_cooperating_then_copies_opponent_previous_choice() -> None:
    strategy = TitForTat()
    memory = PlayerMemory()
    assert strategy.choose(memory) is Choice.COOPERATE

    memory.observations.append(observation(Choice.COOPERATE, Choice.DEFECT))
    assert strategy.choose(memory) is Choice.DEFECT


def test_grim_trigger_defects_forever_after_any_opponent_defection() -> None:
    strategy = GrimTrigger()
    memory = PlayerMemory()
    assert strategy.choose(memory) is Choice.COOPERATE

    memory.observations.append(observation(Choice.COOPERATE, Choice.DEFECT))
    assert strategy.choose(memory) is Choice.DEFECT

    memory.observations.append(observation(Choice.DEFECT, Choice.COOPERATE))
    assert strategy.choose(memory) is Choice.DEFECT


def test_random_strategy_uses_injected_rng_for_determinism() -> None:
    strategy = RandomStrategy(rng=random.Random(1))

    choices = [strategy.choose(PlayerMemory()) for _ in range(4)]

    assert choices == [
        Choice.COOPERATE,
        Choice.COOPERATE,
        Choice.DEFECT,
        Choice.COOPERATE,
    ]


def test_generous_tit_for_tat_sometimes_forgives_defection() -> None:
    forgiving = GenerousTitForTat(rng=random.Random(1), forgiveness_probability=1.0)
    punitive = GenerousTitForTat(rng=random.Random(1), forgiveness_probability=0.0)
    memory = PlayerMemory([observation(Choice.COOPERATE, Choice.DEFECT)])

    assert forgiving.choose(memory) is Choice.COOPERATE
    assert punitive.choose(memory) is Choice.DEFECT
