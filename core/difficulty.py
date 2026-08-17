"""
Adaptive difficulty engine.

Tracks rolling accuracy per player (overall, and optionally per category) and
nudges the next question's difficulty up or down — this is what makes every
match feel personalized instead of fully random, per the original design doc's
'AI Difficulty Engine' section (implemented as a lightweight rule-based
controller rather than a trained model, which is the right amount of
complexity for a per-question adaptive loop).
"""
from __future__ import annotations

LADDER = ["Easy", "Medium", "Hard", "Expert"]

PROMOTE_THRESHOLD = 0.75   # accuracy above this -> move up
DEMOTE_THRESHOLD = 0.40    # accuracy below this -> move down
WINDOW = 5                 # look at the last N answers


class DifficultyEngine:
    def __init__(self, start: str = "Easy"):
        self.level_index = LADDER.index(start)
        self.history: list[bool] = []  # True = correct

    @property
    def current_difficulty(self) -> str:
        return LADDER[self.level_index]

    def record(self, correct: bool) -> None:
        self.history.append(correct)
        self.history = self.history[-WINDOW:]
        if len(self.history) < 3:
            return
        acc = sum(self.history) / len(self.history)
        if acc >= PROMOTE_THRESHOLD and self.level_index < len(LADDER) - 1:
            self.level_index += 1
            self.history = []
        elif acc <= DEMOTE_THRESHOLD and self.level_index > 0:
            self.level_index -= 1
            self.history = []

    def accuracy(self) -> float:
        if not self.history:
            return 0.0
        return round(100 * sum(self.history) / len(self.history), 1)
