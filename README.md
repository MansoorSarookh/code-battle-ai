# ⚔️ Code Battle AI

A full local implementation of a 2-player competitive programming game, built with
Streamlit + SQLite, with optional AI-generated questions (Anthropic API).

## What's implemented (real, working)

- **Game engine**: 10-round matches, hot-seat 2-player, turn/round/state management
- **8 challenge types**: MCQ, True/False, Output Prediction, Code Completion,
  Debugging, Complexity (Big-O), Short Answer, and a Code-Writing "Final Boss" round
- **Dynamic scoring**: base points + speed bonus + difficulty multiplier
- **Combo/streak system** with bonus points, resettable by wrong answers
- **Power-ups**: 50/50, Hint, Double Points, Shield — earned via streaks, limited per match
- **Adaptive difficulty engine**: per-category accuracy tracked and used to pick the
  next question's difficulty per player
- **AI question generation** (optional): if you provide an Anthropic API key, new
  questions are generated on the fly, validated against a strict JSON schema, and
  checked for safety before ever reaching a player. If no key is provided, or
  generation/validation fails, the game falls back to the curated local bank —
  the AI is never allowed to "blindly" reach the screen.
- **AI hints** (graduated, cost points), **AI explanations** after each answer,
  **AI post-match coach report** (weak/strong topic breakdown + recommendation)
- **Player profiles**: XP, levels, simple Elo-style rating, best streak, win rate
- **Leaderboard** (global, persisted in SQLite)
- **Achievements**: first win, streak badges, speed badges, etc.
- **Practice mode / Daily Challenge**
- **Dark "coding arena" UI**: custom CSS, JetBrains Mono for code, animated score
  pop-ups, streak fire, progress bars, victory screen
- **Local code-writing round** with a *restricted* sandboxed executor (timeout +
  restricted builtins/globals) and unit-test style scoring

## What's deliberately NOT implemented, and why

The original spec asks for a few things that are genuinely separate infrastructure
projects, not features you bolt onto a single Streamlit script honestly:

- **True real-time online multiplayer (WebSockets, two separate browsers)** —
  Streamlit's execution model is single-session request/rerun, not a persistent
  socket server. This app implements **local hot-seat 2-player** (both players share
  one screen/device, alternating turns) which reproduces the actual game rules and
  scoring faithfully. To go fully online you'd add a small FastAPI/WebSocket backend
  as the source of truth and have two Streamlit (or plain web) clients subscribe to
  it — that's a distinct backend service, not a Streamlit feature.
- **Production-grade sandboxed code execution (Docker/gVisor/Firecracker per
  submission)** — real isolation needs OS-level containers or a microVM, which this
  environment can't provision for you. The code-writing round here uses timeouts and
  a restricted builtins/globals dict, which is fine for **local, single-user/trusted
  hot-seat play** but is explicitly **not** safe to expose on a public multiplayer
  server. `security/code_sandbox.py` documents exactly where to swap in a real
  container runner.
- **PostgreSQL** — SQLite is used since this runs as a single local file-based app;
  swapping the `database.py` layer for `psycopg2`/`SQLAlchemy` + Postgres is a
  connection-string change, not a redesign, if you later deploy this as a hosted
  service with concurrent writers.
- **Sound effects** — omitted since this environment can't ship binary audio assets;
  hooks are left in `ui/styles.py` (`play_sound()` is a no-op you can wire to local
  mp3 files).

## Running it

```bash
cd code-battle-ai
pip install -r requirements.txt
streamlit run app.py
```

First run creates `codebattle.db` (SQLite) automatically. AI features are optional —
paste an Anthropic API key into the sidebar to enable AI-generated questions, hints,
explanations, and the post-match coach. Without a key, everything else works off the
curated local question bank (60+ hand-written questions across 8 categories and 4
difficulty tiers).

## Project layout

```
code-battle-ai/
├── app.py                     # Streamlit entrypoint / all screens
├── core/
│   ├── game_engine.py         # Match/round/turn state machine
│   ├── scoring.py             # Points, speed bonus, multipliers, streaks
│   ├── difficulty.py          # Adaptive difficulty engine
│   ├── elo.py                 # Rating updates
│   └── achievements.py        # Achievement definitions + checker
├── data/
│   ├── database.py            # SQLite schema + repository functions
│   └── questions_bank.py      # 60+ curated questions, all types/difficulties
├── ai/
│   └── generator.py           # AI question gen + validation + hints/coach
├── security/
│   └── code_sandbox.py        # Restricted local code execution + test runner
└── ui/
    └── styles.py               # Dark "coding arena" CSS theme
```
