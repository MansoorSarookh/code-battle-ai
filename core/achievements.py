"""Achievement definitions + a checker that runs after each match."""
from __future__ import annotations

ACHIEVEMENTS = {
    "first_win":        {"name": "🏅 First Victory",   "desc": "Win your first match."},
    "on_fire":          {"name": "🔥 On Fire",          "desc": "Get 5 correct answers in a row."},
    "unstoppable":      {"name": "🔥🔥 Unstoppable",     "desc": "Get 10 correct answers in a row."},
    "speed_demon":      {"name": "⚡ Speed Demon",       "desc": "Answer correctly within 3 seconds."},
    "bug_hunter":       {"name": "🐛 Bug Hunter",        "desc": "Solve 10 debugging challenges correctly (lifetime)."},
    "algorithm_master": {"name": "🧠 Algorithm Master",  "desc": "Reach 90%+ accuracy in Algorithms & DS (min. 10 attempts)."},
    "code_king":        {"name": "👑 Code King",         "desc": "Reach 2000 rating."},
    "boss_slayer":      {"name": "👑 Boss Slayer",       "desc": "Pass a Final Boss code-writing round."},
    "perfectionist":    {"name": "💎 Perfectionist",     "desc": "Win a match without a single wrong answer."},
}


def check_match_achievements(
    *,
    won: bool,
    best_streak_this_match: int,
    fastest_correct_time: float | None,
    zero_mistakes: bool,
    passed_final_boss: bool,
    lifetime_rating: int,
    lifetime_debugging_correct: int,
    algo_accuracy: float | None,
    algo_attempts: int,
) -> list[str]:
    """Returns achievement ids newly qualified for (caller still checks DB for already-earned)."""
    earned = []
    if won:
        earned.append("first_win")
    if best_streak_this_match >= 5:
        earned.append("on_fire")
    if best_streak_this_match >= 10:
        earned.append("unstoppable")
    if fastest_correct_time is not None and fastest_correct_time <= 3.0:
        earned.append("speed_demon")
    if lifetime_debugging_correct >= 10:
        earned.append("bug_hunter")
    if algo_attempts >= 10 and algo_accuracy is not None and algo_accuracy >= 90.0:
        earned.append("algorithm_master")
    if lifetime_rating >= 2000:
        earned.append("code_king")
    if passed_final_boss:
        earned.append("boss_slayer")
    if won and zero_mistakes:
        earned.append("perfectionist")
    return earned
