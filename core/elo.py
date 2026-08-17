"""Simple Elo-style rating update, used at the end of a Ranked match."""
from __future__ import annotations

K_FACTOR = 32


def expected_score(rating_a: int, rating_b: int) -> float:
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def rating_deltas(rating1: int, rating2: int, player1_won: bool | None) -> tuple[int, int]:
    """player1_won: True/False, or None for a draw."""
    exp1 = expected_score(rating1, rating2)
    exp2 = 1 - exp1
    if player1_won is None:
        actual1, actual2 = 0.5, 0.5
    elif player1_won:
        actual1, actual2 = 1.0, 0.0
    else:
        actual1, actual2 = 0.0, 1.0
    delta1 = round(K_FACTOR * (actual1 - exp1))
    delta2 = round(K_FACTOR * (actual2 - exp2))
    return delta1, delta2
