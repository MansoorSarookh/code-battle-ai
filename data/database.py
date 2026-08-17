"""
SQLite persistence layer for Code Battle AI.

Kept deliberately as a thin repository layer (plain functions, plain SQL) rather
than an ORM, so it's trivial to read, and trivial to swap for Postgres later
(the only thing that changes is the connection object + placeholder style).
"""
from __future__ import annotations

import sqlite3
import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "codebattle.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    name            TEXT PRIMARY KEY,
    rating          INTEGER NOT NULL DEFAULT 1200,
    xp              INTEGER NOT NULL DEFAULT 0,
    level           INTEGER NOT NULL DEFAULT 1,
    matches_played  INTEGER NOT NULL DEFAULT 0,
    matches_won     INTEGER NOT NULL DEFAULT 0,
    best_streak     INTEGER NOT NULL DEFAULT 0,
    created_at      REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS matches (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    player1         TEXT NOT NULL,
    player2         TEXT NOT NULL,
    mode            TEXT NOT NULL,
    winner          TEXT,
    score1          INTEGER NOT NULL DEFAULT 0,
    score2          INTEGER NOT NULL DEFAULT 0,
    played_at       REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS question_attempts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id        INTEGER,
    player          TEXT NOT NULL,
    category        TEXT NOT NULL,
    difficulty      TEXT NOT NULL,
    question_type   TEXT NOT NULL,
    correct         INTEGER NOT NULL,
    time_taken      REAL NOT NULL,
    points_earned   INTEGER NOT NULL,
    created_at      REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS player_skills (
    player          TEXT NOT NULL,
    category        TEXT NOT NULL,
    correct         INTEGER NOT NULL DEFAULT 0,
    total           INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player, category)
);

CREATE TABLE IF NOT EXISTS achievements_earned (
    player          TEXT NOT NULL,
    achievement_id  TEXT NOT NULL,
    earned_at       REAL NOT NULL,
    PRIMARY KEY (player, achievement_id)
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def ensure_player(name: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO players (name, created_at) VALUES (?, ?)",
            (name, time.time()),
        )


def get_player(name: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM players WHERE name = ?", (name,))
        return cur.fetchone()


def update_player_after_match(
    name: str,
    rating_delta: int,
    xp_gain: int,
    won: bool,
    streak_reached: int,
) -> None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM players WHERE name = ?", (name,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO players (name, created_at) VALUES (?, ?)", (name, time.time())
            )
            row = conn.execute("SELECT * FROM players WHERE name = ?", (name,)).fetchone()

        new_xp = row["xp"] + xp_gain
        new_level = 1 + int((new_xp) ** 0.5 // 5)  # smooth XP curve
        new_best_streak = max(row["best_streak"], streak_reached)

        conn.execute(
            """UPDATE players SET
                 rating = MAX(100, rating + ?),
                 xp = ?,
                 level = ?,
                 matches_played = matches_played + 1,
                 matches_won = matches_won + ?,
                 best_streak = ?
               WHERE name = ?""",
            (rating_delta, new_xp, new_level, 1 if won else 0, new_best_streak, name),
        )


def record_match(player1: str, player2: str, mode: str, winner: str, score1: int, score2: int) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO matches (player1, player2, mode, winner, score1, score2, played_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (player1, player2, mode, winner, score1, score2, time.time()),
        )
        return cur.lastrowid


def record_attempt(
    match_id: Optional[int],
    player: str,
    category: str,
    difficulty: str,
    question_type: str,
    correct: bool,
    time_taken: float,
    points_earned: int,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO question_attempts
               (match_id, player, category, difficulty, question_type, correct,
                time_taken, points_earned, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (match_id, player, category, difficulty, question_type, int(correct),
             time_taken, points_earned, time.time()),
        )
        conn.execute(
            """INSERT INTO player_skills (player, category, correct, total)
               VALUES (?, ?, ?, 1)
               ON CONFLICT(player, category) DO UPDATE SET
                 correct = correct + excluded.correct,
                 total = total + 1""",
            (player, category, int(correct)),
        )


def get_skill_breakdown(player: str) -> dict[str, dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT category, correct, total FROM player_skills WHERE player = ?", (player,)
        ).fetchall()
    return {
        r["category"]: {
            "correct": r["correct"],
            "total": r["total"],
            "accuracy": round(100 * r["correct"] / r["total"], 1) if r["total"] else 0.0,
        }
        for r in rows
    }


def get_leaderboard(limit: int = 10) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM players ORDER BY rating DESC, xp DESC LIMIT ?", (limit,)
        ).fetchall()


def grant_achievement(player: str, achievement_id: str) -> bool:
    """Returns True if this is a newly earned achievement."""
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO achievements_earned (player, achievement_id, earned_at) VALUES (?, ?, ?)",
                (player, achievement_id, time.time()),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def get_achievements(player: str) -> set[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT achievement_id FROM achievements_earned WHERE player = ?", (player,)
        ).fetchall()
    return {r["achievement_id"] for r in rows}
