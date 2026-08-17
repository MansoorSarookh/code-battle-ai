"""
Core match state machine. Framework-agnostic (no Streamlit imports) so it's
testable and reusable — app.py just drives it from session_state.

Hot-seat flow per round (see README for why this replaces true simultaneous
online play): the SAME question is shown to Player 1, then privately to
Player 2 after a hand-off screen, each individually timed — the original
"first correct gets more points" idea is preserved via each player's own
speed bonus rather than a race, since only one physical screen is available.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from core.difficulty import DifficultyEngine
from core.scoring import score_answer

TOTAL_ROUNDS = 10
FINAL_BOSS_ROUND = TOTAL_ROUNDS  # last round is the code-writing final boss

POWERUP_COSTS = {"fifty_fifty": 0, "hint": 0, "double_points": 0, "shield": 0}  # earned, not bought
POWERUPS_PER_STREAK_MILESTONE = {5: "double_points", 8: "shield", 10: "fifty_fifty"}


class Phase(Enum):
    HOME = auto()
    P1_TURN = auto()
    HANDOFF = auto()
    P2_TURN = auto()
    REVEAL = auto()
    FINAL_BOSS_P1 = auto()
    FINAL_BOSS_HANDOFF = auto()
    FINAL_BOSS_P2 = auto()
    FINAL_BOSS_REVEAL = auto()
    POST_MATCH = auto()


@dataclass
class PlayerMatchState:
    name: str
    score: int = 0
    streak: int = 0
    best_streak: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    fastest_correct_time: float | None = None
    powerups: dict = field(default_factory=lambda: {"fifty_fifty": 0, "hint": 0, "double_points": 0, "shield": 0})
    active_double_points: bool = False
    shield_active: bool = False
    difficulty_engine: DifficultyEngine = field(default_factory=DifficultyEngine)
    seen_question_ids: set = field(default_factory=set)
    category_log: list = field(default_factory=list)  # list of (category, correct, difficulty, type)

    def award_streak_powerups(self) -> str | None:
        milestone = POWERUPS_PER_STREAK_MILESTONE.get(self.streak)
        if milestone:
            self.powerups[milestone] += 1
            return milestone
        return None

    def apply_answer(self, correct: bool, difficulty: str, time_taken: float, time_limit: float,
                      category: str, qtype: str, hint_penalty: int = 0) -> dict:
        if not correct and self.shield_active:
            # shield absorbs the streak break (but not the point loss) once
            self.shield_active = False
            self.powerups["shield"] = max(0, self.powerups["shield"] - 1)
            result = score_answer(False, difficulty, time_taken, time_limit, self.streak, hint_penalty)
            result["points"] = 0  # shield also negates the penalty
            result["shielded"] = True
        else:
            result = score_answer(correct, difficulty, time_taken, time_limit, self.streak,
                                   hint_penalty, self.active_double_points)
            result["shielded"] = False

        self.active_double_points = False
        self.score = max(0, self.score + result["points"])

        if correct:
            self.correct_count += 1
            self.streak = result.get("new_streak", self.streak + 1)
            self.best_streak = max(self.best_streak, self.streak)
            if self.fastest_correct_time is None or time_taken < self.fastest_correct_time:
                self.fastest_correct_time = time_taken
            earned_powerup = self.award_streak_powerups()
            result["powerup_earned"] = earned_powerup
        else:
            if not result["shielded"]:
                self.wrong_count += 1
                self.streak = 0
            result["powerup_earned"] = None

        self.difficulty_engine.record(correct)
        self.category_log.append({"category": category, "correct": correct, "difficulty": difficulty, "type": qtype})
        return result


ROUND_THEMES = {
    1: ("Warm-Up", None),
    2: ("Output Prediction", ["python_basics", "lists_strings"]),
    3: ("Loops & Control", ["loops_control"]),
    4: ("Debugging", ["debugging"]),
    5: ("OOP & Functions", ["functions_oop"]),
    6: ("Algorithms", ["algorithms_ds"]),
    7: ("Complexity", ["complexity"]),
    8: ("Databases & Web", ["databases_web"]),
    9: ("Hard Challenge", None),
    10: ("FINAL BOSS", None),
}


@dataclass
class Match:
    player1: str
    player2: str
    mode: str = "Ranked"  # Ranked | Casual | Practice
    round_number: int = 1
    phase: Phase = Phase.HOME
    p1: PlayerMatchState = None
    p2: PlayerMatchState = None
    round_category: str | None = None
    current_question: dict | None = None
    current_code_challenge: dict | None = None
    p1_round_result: dict | None = None
    p2_round_result: dict | None = None
    finished: bool = False
    solo: bool = False
    forced_category: str | None = None

    def __post_init__(self):
        if self.p1 is None:
            self.p1 = PlayerMatchState(name=self.player1)
        if self.p2 is None:
            self.p2 = PlayerMatchState(name=self.player2)

    def is_final_boss_round(self) -> bool:
        return self.round_number == FINAL_BOSS_ROUND

    def winner(self) -> str | None:
        if self.p1.score > self.p2.score:
            return self.player1
        if self.p2.score > self.p1.score:
            return self.player2
        return None  # draw

    def advance_round(self) -> None:
        self.round_number += 1
        self.current_question = None
        self.current_code_challenge = None
        self.p1_round_result = None
        self.p2_round_result = None
        if self.round_number > TOTAL_ROUNDS:
            self.finished = True
            self.phase = Phase.POST_MATCH
        else:
            self.phase = Phase.FINAL_BOSS_P1 if self.is_final_boss_round() else Phase.P1_TURN
