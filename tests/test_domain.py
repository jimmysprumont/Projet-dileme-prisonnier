from prisoners_dilemma.domain import Choice, PayoffMatrix, score_round


def test_standard_payoff_matrix_scores_each_choice_pair() -> None:
    matrix = PayoffMatrix.standard()

    assert score_round(Choice.COOPERATE, Choice.COOPERATE, matrix) == (3, 3)
    assert score_round(Choice.COOPERATE, Choice.DEFECT, matrix) == (0, 5)
    assert score_round(Choice.DEFECT, Choice.COOPERATE, matrix) == (5, 0)
    assert score_round(Choice.DEFECT, Choice.DEFECT, matrix) == (1, 1)


def test_choice_from_token_accepts_short_and_long_values() -> None:
    assert Choice.from_token("C") is Choice.COOPERATE
    assert Choice.from_token("cooperate") is Choice.COOPERATE
    assert Choice.from_token("D") is Choice.DEFECT
    assert Choice.from_token("defect") is Choice.DEFECT
