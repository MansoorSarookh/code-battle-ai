"""Dynamic scoring: base points + speed bonus + difficulty multiplier + streak bonus."""
from __future__ import annotations

DIFFICULTY_MULTIPLIER = {"Easy": 1.0, "Medium": 1.5, "Hard": 2.0, "Expert": 3.0}
BASE_POINTS = 100
MAX_SPEED_BONUS = 50
STREAK_BONUS_EVERY = 5
STREAK_BONUS_POINTS = 50
WRONG_PENALTY = 20


def speed_bonus(time_taken: float, time_limit: float) -> int:
    """Linear bonus: full 50 if answered instantly, 0 if used the whole time limit."""
    if time_limit <= 0:
        return 0
    frac_remaining = max(0.0, (time_limit - time_taken) / time_limit)
    return round(MAX_SPEED_BONUS * frac_remaining)


def score_answer(
    correct: bool,
    difficulty: str,
    time_taken: float,
    time_limit: float,
    current_streak: int,
    hint_penalty: int = 0,
    double_points_active: bool = False,
) -> dict:
    """Returns a breakdown dict: {points, base, speed, streak_bonus, multiplier, correct}."""
    if not correct:
        return {
            "correct": False, "points": -WRONG_PENALTY, "base": 0, "speed": 0,
            "streak_bonus": 0, "multiplier": 0, "streak_hit": False,
        }

    multiplier = DIFFICULTY_MULTIPLIER.get(difficulty, 1.0)
    base = BASE_POINTS
    speed = speed_bonus(time_taken, time_limit)
    raw = round((base + speed) * multiplier)

    new_streak = current_streak + 1
    streak_bonus = STREAK_BONUS_POINTS if new_streak % STREAK_BONUS_EVERY == 0 else 0

    total = raw + streak_bonus - hint_penalty
    if double_points_active:
        total *= 2

    return {
        "correct": True,
        "points": max(0, total),
        "base": base,
        "speed": speed,
        "streak_bonus": streak_bonus,
        "multiplier": multiplier,
        "streak_hit": streak_bonus > 0,
        "new_streak": new_streak,
    }
