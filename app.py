"""
⚔️ Code Battle AI — Streamlit entrypoint.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import random
import time
from datetime import date

import streamlit as st

from data import database as db
from data.questions_bank import (
    CATEGORIES, DIFFICULTIES, pick_question, pick_code_challenge, QUESTIONS,
)
from core.game_engine import Match, PlayerMatchState, Phase, ROUND_THEMES, TOTAL_ROUNDS
from core.scoring import DIFFICULTY_MULTIPLIER
from core.elo import rating_deltas
from core.achievements import ACHIEVEMENTS, check_match_achievements
from ai import generator as ai
from security.code_sandbox import run_test_suite
from ui.styles import inject_css, player_card_html, timer_html, play_sound

st.set_page_config(page_title="Code Battle AI", page_icon="⚔️", layout="centered")
db.init_db()
inject_css()

# ------------------------------------------------------------------ session state
def init_state() -> None:
    defaults = {
        "screen": "home",
        "match": None,
        "api_key": "",
        "question_start": None,
        "removed_options": None,  # 50/50 result for the current question, per turn
        "hint_text": None,
        "hint_cost": 0,
        "timed_out": False,
        "code_result": None,
        "player1_name": "Mansoor",
        "player2_name": "Player 2",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ------------------------------------------------------------------ helpers
def elapsed() -> float:
    if st.session_state.question_start is None:
        return 0.0
    return time.time() - st.session_state.question_start


def start_timer() -> None:
    st.session_state.question_start = time.time()
    st.session_state.removed_options = None
    st.session_state.hint_text = None
    st.session_state.hint_cost = 0
    st.session_state.timed_out = False


def current_player_state(match: Match) -> PlayerMatchState:
    return match.p1 if match.phase in (Phase.P1_TURN, Phase.FINAL_BOSS_P1) else match.p2


def pick_round_question(match: Match, pstate: PlayerMatchState) -> dict:
    theme_name, pool = ROUND_THEMES.get(match.round_number, ("Battle", None))
    category = match.forced_category or (random.choice(pool) if pool else None)
    difficulty = pstate.difficulty_engine.current_difficulty
    if match.round_number == 9:  # Hard Challenge round: bump difficulty floor
        idx = max(DIFFICULTIES.index(difficulty), DIFFICULTIES.index("Hard"))
        difficulty = DIFFICULTIES[idx]

    q = None
    if st.session_state.api_key and random.random() < 0.35:  # occasionally mix in an AI question
        lang = "Python"
        topic = category or random.choice(CATEGORIES)
        q = ai.generate_question(st.session_state.api_key, lang, topic, difficulty)
    if q is None:
        q = pick_question(difficulty, pstate.seen_question_ids, category=category)
    pstate.seen_question_ids.add(q["id"])
    return q


def options_for_display(question: dict) -> list[str]:
    if question["type"] == "true_false":
        return ["True", "False"]
    return question["options"]


def is_correct(question: dict, choice_index: int | None, text_answer: str | None) -> bool:
    if question["type"] == "true_false":
        return (choice_index == 0) == question["correct"]
    if question["type"] == "short_answer":
        if text_answer is None:
            return False
        accepted = [a.lower().strip() for a in question.get("accept", [question["correct"]])]
        return text_answer.lower().strip() in accepted
    return choice_index == question["correct"]


# ------------------------------------------------------------------ small UI fragments
@st.fragment(run_every=1)
def render_timer(time_limit: float, key: str):
    remaining = time_limit - elapsed()
    st.markdown(timer_html(remaining), unsafe_allow_html=True)
    st.progress(max(0.0, min(1.0, remaining / time_limit)))
    if remaining <= 0 and not st.session_state.timed_out:
        st.session_state.timed_out = True
        st.rerun()


# ------------------------------------------------------------------ HOME
def screen_home():
    st.markdown(
        "<h1 style='text-align:center;'>⚔️ CODE BATTLE AI</h1>"
        "<p style='text-align:center;opacity:0.7;'>ENTER THE CODING ARENA</p>",
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Mode", ["⚔️ Ranked Battle (2P hot-seat)", "🎮 Casual Battle (2P hot-seat)",
                  "🧠 Practice (solo)", "🤖 AI Training (solo, pick weak topic)"],
        horizontal=False,
    )
    solo = mode.startswith("🧠") or mode.startswith("🤖")

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.player1_name = st.text_input("🔴 Player 1", st.session_state.player1_name)
    with c2:
        if not solo:
            st.session_state.player2_name = st.text_input("🔵 Player 2", st.session_state.player2_name)

    forced_category = None
    if mode.startswith("🤖"):
        forced_category = st.selectbox("Focus topic", CATEGORIES, format_func=lambda c: c.replace("_", " ").title())

    if st.button("⚔️ ENTER ARENA", type="primary", width='stretch'):
        p1 = st.session_state.player1_name.strip() or "Player 1"
        p2 = "AI Ghost" if solo else (st.session_state.player2_name.strip() or "Player 2")
        db.ensure_player(p1)
        if not solo:
            db.ensure_player(p2)
        match_mode = "Ranked" if mode.startswith("⚔️") else ("Casual" if mode.startswith("🎮") else "Practice")
        match = Match(player1=p1, player2=p2, mode=match_mode, solo=solo, forced_category=forced_category)
        match.phase = Phase.P1_TURN
        st.session_state.match = match
        start_timer()
        st.session_state.screen = "arena"
        st.rerun()

    st.divider()
    if st.button("🌅 Daily Challenge", width='stretch'):
        st.session_state.screen = "daily"
        st.rerun()

    ph1, ph2 = st.columns(2)
    with ph1:
        if st.button("🏆 Leaderboard", width='stretch'):
            st.session_state.screen = "leaderboard"; st.rerun()
    with ph2:
        if st.button("👤 Profile", width='stretch'):
            st.session_state.screen = "profile"; st.rerun()


# ------------------------------------------------------------------ QUESTION RENDERING (shared)
def render_question_panel(match: Match, pstate: PlayerMatchState):
    q = match.current_question
    theme_name, _ = ROUND_THEMES.get(match.round_number, ("Battle", None))
    color = "red" if pstate is match.p1 else "blue"

    st.markdown(f"<div class='round-pill'>Round {match.round_number} / {TOTAL_ROUNDS} · {theme_name}</div>",
                unsafe_allow_html=True)
    st.markdown(player_card_html(pstate.name, pstate.score, None, color), unsafe_allow_html=True)

    if pstate.streak >= 2:
        st.markdown(f"<div class='streak-banner'>🔥 STREAK ×{pstate.streak}</div>", unsafe_allow_html=True)

    render_timer(q["time_limit"], key=f"timer_{match.round_number}_{color}")

    cat_label = q["category"].replace("_", " ").title()
    st.markdown(
        f"<span class='category-tag'>{cat_label}</span>"
        f"<span class='difficulty-tag diff-{q['difficulty']}'>{q['difficulty']}</span>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='question-box'>", unsafe_allow_html=True)
    st.markdown(f"<div class='question-text'>{q['question']}</div>", unsafe_allow_html=True)
    if q.get("code"):
        st.code(q["code"], language="python")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.hint_text:
        st.info(f"💡 Hint: {st.session_state.hint_text}")

    # power-up row
    render_powerups(pstate, q)

    disabled = st.session_state.timed_out
    if q["type"] == "short_answer":
        answer = st.text_input("Your answer", key=f"sa_{match.round_number}_{color}", disabled=disabled)
        if st.button("Submit", disabled=disabled, width='stretch'):
            submit_answer(match, pstate, q, None, answer)
    else:
        options = options_for_display(q)
        removed = st.session_state.removed_options or set()
        cols = st.columns(len(options))
        labels = ["A", "B", "C", "D"]
        for i, (col, opt) in enumerate(zip(cols, options)):
            with col:
                if i in removed:
                    st.button(f"{labels[i]}. —", disabled=True, key=f"opt_{match.round_number}_{color}_{i}",
                               width='stretch')
                else:
                    if st.button(f"{labels[i]}. {opt}", disabled=disabled,
                                  key=f"opt_{match.round_number}_{color}_{i}", width='stretch'):
                        submit_answer(match, pstate, q, i, None)

    if st.session_state.timed_out:
        st.error("⏰ Time's up!")
        if st.button("Continue", width='stretch'):
            submit_answer(match, pstate, q, None, None, forced_timeout=True)


def render_powerups(pstate: PlayerMatchState, q: dict):
    pu = pstate.powerups
    cols = st.columns(4)
    with cols[0]:
        if st.button(f"🧠 50/50 ({pu['fifty_fifty']})", disabled=pu["fifty_fifty"] <= 0 or q["type"] == "short_answer"):
            use_fifty_fifty(pstate, q)
    with cols[1]:
        if st.button(f"🔍 Hint ({pu['hint']})", disabled=pu["hint"] <= 0):
            use_hint(pstate, q)
    with cols[2]:
        if st.button(f"⚡ 2× ({pu['double_points']})", disabled=pu["double_points"] <= 0 or pstate.active_double_points):
            pu["double_points"] -= 1
            pstate.active_double_points = True
            st.rerun()
    with cols[3]:
        if st.button(f"🛡️ Shield ({pu['shield']})", disabled=pu["shield"] <= 0 or pstate.shield_active):
            pu["shield"] -= 1
            pstate.shield_active = True
            st.rerun()


def use_fifty_fifty(pstate: PlayerMatchState, q: dict):
    correct_idx = 0 if q["type"] == "true_false" else q["correct"]
    n_options = 2 if q["type"] == "true_false" else len(q["options"])
    wrong_indices = [i for i in range(n_options) if i != correct_idx]
    to_remove = set(random.sample(wrong_indices, min(2, len(wrong_indices))))
    st.session_state.removed_options = to_remove
    pstate.powerups["fifty_fifty"] -= 1
    st.rerun()


def use_hint(pstate: PlayerMatchState, q: dict):
    pstate.powerups["hint"] -= 1
    text = ai.generate_hint(st.session_state.api_key, q, 1) if st.session_state.api_key else None
    if not text:
        explanation = q.get("explanation", "")
        text = explanation[: max(20, len(explanation) // 2)] + "…"
    st.session_state.hint_text = text
    st.session_state.hint_cost += 20
    st.rerun()


def submit_answer(match: Match, pstate: PlayerMatchState, q: dict, choice_index, text_answer, forced_timeout=False):
    time_taken = q["time_limit"] if forced_timeout else min(elapsed(), q["time_limit"])
    correct = False if forced_timeout else is_correct(q, choice_index, text_answer)
    result = pstate.apply_answer(
        correct, q["difficulty"], time_taken, q["time_limit"],
        q["category"], q["type"], hint_penalty=st.session_state.hint_cost,
    )
    result["question"] = q
    if pstate is match.p1:
        match.p1_round_result = result
        match.phase = Phase.REVEAL if match.solo else Phase.HANDOFF
    else:
        match.p2_round_result = result
        match.phase = Phase.REVEAL
    st.rerun()


# ------------------------------------------------------------------ ARENA dispatch
def screen_arena():
    match: Match = st.session_state.match

    if match.phase in (Phase.P1_TURN, Phase.P2_TURN):
        pstate = current_player_state(match)
        if match.current_question is None:
            match.current_question = pick_round_question(match, pstate)
            start_timer()
        render_question_panel(match, pstate)

    elif match.phase == Phase.HANDOFF:
        st.markdown(
            f"<div class='handoff-box'><h2>🔄 Pass the device</h2>"
            f"<p style='opacity:0.75'>🔵 {match.player2}, get ready...</p></div>",
            unsafe_allow_html=True,
        )
        if st.button("🔵 I'm ready!", type="primary", width='stretch'):
            match.phase = Phase.P2_TURN
            start_timer()
            st.rerun()

    elif match.phase == Phase.REVEAL:
        render_reveal(match)

    elif match.phase in (Phase.FINAL_BOSS_P1, Phase.FINAL_BOSS_P2):
        render_final_boss(match)

    elif match.phase == Phase.FINAL_BOSS_HANDOFF:
        st.markdown(
            f"<div class='handoff-box'><h2>👑 Pass the device for the FINAL BOSS</h2>"
            f"<p style='opacity:0.75'>🔵 {match.player2}, get ready...</p></div>",
            unsafe_allow_html=True,
        )
        if st.button("🔵 I'm ready!", type="primary", width='stretch'):
            match.phase = Phase.FINAL_BOSS_P2
            start_timer()
            st.rerun()

    elif match.phase == Phase.FINAL_BOSS_REVEAL:
        render_final_boss_reveal(match)

    elif match.phase == Phase.POST_MATCH:
        render_post_match(match)


def render_reveal(match: Match):
    st.markdown(f"<div class='round-pill'>Round {match.round_number} Results</div>", unsafe_allow_html=True)

    def block(pstate, result, color):
        q = result["question"]
        flash = "flash-correct" if result["correct"] else "flash-wrong"
        icon = "✅ Correct!" if result["correct"] else ("🛡️ Shielded!" if result.get("shielded") else "❌ Wrong")
        st.markdown(player_card_html(pstate.name, pstate.score, None, color), unsafe_allow_html=True)
        st.markdown(f"<div class='{flash}'>{icon} ({result['points']:+d} pts)</div>", unsafe_allow_html=True)
        if result.get("powerup_earned"):
            st.success(f"🎁 Power-up earned: {result['powerup_earned'].replace('_',' ').title()}!")
        with st.expander("🤖 Explanation", expanded=True):
            explanation = q.get("explanation", "")
            if st.session_state.api_key:
                ai_expl = ai.generate_hint(st.session_state.api_key, q, 2)  # reuse as a short elaboration
            st.write(explanation)

    block(match.p1, match.p1_round_result, "red")
    if not match.solo:
        st.divider()
        block(match.p2, match.p2_round_result, "blue")

    if st.button("➡️ Next Round", type="primary", width='stretch'):
        record_round_to_db(match)
        match.advance_round()
        if not match.finished:
            start_timer()
        st.rerun()


def render_final_boss(match: Match):
    pstate = match.p1 if match.phase == Phase.FINAL_BOSS_P1 else match.p2
    color = "red" if pstate is match.p1 else "blue"
    if match.current_code_challenge is None:
        match.current_code_challenge = pick_code_challenge(set())
        start_timer()
    c = match.current_code_challenge

    st.markdown("<div class='round-pill'>👑 FINAL BOSS</div>", unsafe_allow_html=True)
    st.markdown(player_card_html(pstate.name, pstate.score, None, color), unsafe_allow_html=True)
    render_timer(c["time_limit"], key=f"boss_timer_{color}")

    st.markdown(f"### {c['title']}  <span class='difficulty-tag diff-{c['difficulty']}'>{c['difficulty']}</span>",
                unsafe_allow_html=True)
    st.write(c["prompt"])

    code_key = f"code_{color}"
    if code_key not in st.session_state:
        st.session_state[code_key] = c["starter_code"]
    code = st.text_area("Your code", value=st.session_state[code_key], height=200, key=f"editor_{color}")

    func_name = c["starter_code"].split("(")[0].replace("def ", "").strip()

    if st.button("▶️ Run Tests", width='stretch'):
        st.session_state.code_result = run_test_suite(code, func_name, c["tests"])

    if st.session_state.code_result:
        r = st.session_state.code_result
        st.progress(r["score"] / 100)
        st.write(f"**{r['passed']}/{r['total']} tests passed** ({r['score']}/100)")
        for i, t in enumerate(r["results"]):
            status = "✅" if t["passed"] else "❌"
            st.caption(f"{status} Test {i+1}: input={t['args']} expected={t['expected']!r} got={t['got']!r}"
                       + (f" ({t['error']})" if t["error"] else ""))

    if st.button("🏁 Submit Final Boss Answer", type="primary", width='stretch'):
        r = st.session_state.code_result or run_test_suite(code, func_name, c["tests"])
        time_taken = min(elapsed(), c["time_limit"])
        multiplier = DIFFICULTY_MULTIPLIER.get(c["difficulty"], 3.0)
        points = round(3 * 100 * multiplier * (r["score"] / 100))
        passed_fully = r["score"] == 100
        pstate.score += points
        if passed_fully:
            pstate.correct_count += 1
            pstate.streak += 1
            pstate.best_streak = max(pstate.best_streak, pstate.streak)
        else:
            pstate.wrong_count += 1
            pstate.streak = 0
        pstate.category_log.append({"category": c["category"], "correct": passed_fully,
                                      "difficulty": c["difficulty"], "type": "code_writing"})
        result = {"correct": passed_fully, "points": points, "question": {
            "category": c["category"], "difficulty": c["difficulty"], "type": "code_writing",
            "explanation": f"You passed {r['passed']}/{r['total']} tests.",
        }, "shielded": False, "powerup_earned": None, "test_summary": r}
        if pstate is match.p1:
            match.p1_round_result = result
            match.phase = Phase.REVEAL if match.solo else Phase.FINAL_BOSS_HANDOFF
        else:
            match.p2_round_result = result
            match.phase = Phase.FINAL_BOSS_REVEAL
        st.session_state.code_result = None
        st.rerun()


def render_final_boss_reveal(match: Match):
    render_reveal(match)  # same layout works fine for the boss result


# ------------------------------------------------------------------ DB + post-match
def record_round_to_db(match: Match):
    for pstate, result in [(match.p1, match.p1_round_result), (match.p2, match.p2_round_result)]:
        if result is None:
            continue
        q = result["question"]
        db.record_attempt(
            match_id=None, player=pstate.name, category=q["category"], difficulty=q["difficulty"],
            question_type=q["type"], correct=result["correct"], time_taken=0.0, points_earned=result["points"],
        )


def render_post_match(match: Match):
    record_round_to_db(match)
    winner = match.winner()
    won1 = winner == match.player1

    st.markdown("<div class='victory-title'>🏆 VICTORY!</div>" if winner else
                "<div class='victory-title'>🤝 DRAW!</div>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;font-size:1.3rem;'>{winner or 'Nobody'} wins the match!</p>"
                if winner else "", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(player_card_html(match.p1.name, match.p1.score, None, "red"), unsafe_allow_html=True)
    with c2:
        st.markdown(player_card_html(match.p2.name, match.p2.score, None, "blue"), unsafe_allow_html=True)

    if not st.session_state.get("match_recorded"):
        finalize_match(match)
        st.session_state.match_recorded = True

    st.divider()
    render_skill_radar(match.player1, "🔴 " + match.player1)
    if not match.solo:
        render_skill_radar(match.player2, "🔵 " + match.player2)

    if st.session_state.api_key:
        with st.spinner("AI coach is reviewing the match..."):
            skills = db.get_skill_breakdown(match.player1)
            report = ai.generate_coach_report(st.session_state.api_key, match.player1, skills, won1)
        if report:
            st.markdown("### 🤖 AI Coach Report")
            st.info(report)

    cols = st.columns(2)
    with cols[0]:
        if st.button("🏠 Home", width='stretch'):
            reset_to_home()
    with cols[1]:
        if st.button("🔁 Rematch", width='stretch', type="primary"):
            p1, p2, mode, solo, cat = match.player1, match.player2, match.mode, match.solo, match.forced_category
            reset_to_home(keep_names=True)
            new_match = Match(player1=p1, player2=p2, mode=mode, solo=solo, forced_category=cat)
            new_match.phase = Phase.P1_TURN
            st.session_state.match = new_match
            start_timer()
            st.session_state.screen = "arena"
            st.rerun()


def finalize_match(match: Match):
    winner = match.winner()
    won1 = winner == match.player1
    won2 = winner == match.player2

    if match.mode == "Ranked" and not match.solo:
        p1_row = db.get_player(match.player1)
        p2_row = db.get_player(match.player2)
        r1 = p1_row["rating"] if p1_row else 1200
        r2 = p2_row["rating"] if p2_row else 1200
        player1_won = None if winner is None else won1
        d1, d2 = rating_deltas(r1, r2, player1_won)
    else:
        d1 = d2 = 0

    xp1 = match.p1.correct_count * 15 + match.p1.best_streak * 5 + (50 if won1 else 0)
    xp2 = match.p2.correct_count * 15 + match.p2.best_streak * 5 + (50 if won2 else 0)

    db.update_player_after_match(match.player1, d1, xp1, won1, match.p1.best_streak)
    if not match.solo:
        db.update_player_after_match(match.player2, d2, xp2, won2, match.p2.best_streak)

    db.record_match(match.player1, match.player2, match.mode, winner or "Draw", match.p1.score, match.p2.score)

    grant_achievements_for(match, match.p1, won1)
    if not match.solo:
        grant_achievements_for(match, match.p2, won2)


def grant_achievements_for(match: Match, pstate: PlayerMatchState, won: bool):
    skills = db.get_skill_breakdown(pstate.name)
    debug_correct = skills.get("debugging", {}).get("correct", 0)
    algo = skills.get("algorithms_ds", {})
    p_row = db.get_player(pstate.name)
    ids = check_match_achievements(
        won=won, best_streak_this_match=pstate.best_streak,
        fastest_correct_time=pstate.fastest_correct_time,
        zero_mistakes=(pstate.wrong_count == 0),
        passed_final_boss=any(l["type"] == "code_writing" and l["correct"] for l in pstate.category_log),
        lifetime_rating=p_row["rating"] if p_row else 1200,
        lifetime_debugging_correct=debug_correct,
        algo_accuracy=algo.get("accuracy"), algo_attempts=algo.get("total", 0),
    )
    for aid in ids:
        if db.grant_achievement(pstate.name, aid):
            st.toast(f"🏅 {pstate.name} earned: {ACHIEVEMENTS[aid]['name']}!")


def render_skill_radar(player: str, label: str):
    import plotly.graph_objects as go
    skills = db.get_skill_breakdown(player)
    if not skills:
        return
    cats = list(skills.keys())
    accs = [skills[c]["accuracy"] for c in cats]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=accs, theta=[c.replace("_", " ").title() for c in cats], fill="toself",
                                    name=label, line_color="#6c5ce7"))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        showlegend=False, title=label, height=350,
                        paper_bgcolor="rgba(0,0,0,0)", font_color="#e6e8f0")
    st.plotly_chart(fig, width='stretch')


def reset_to_home(keep_names: bool = False):
    p1, p2 = st.session_state.player1_name, st.session_state.player2_name
    st.session_state.match = None
    st.session_state.match_recorded = False
    st.session_state.screen = "home"
    if keep_names:
        st.session_state.player1_name, st.session_state.player2_name = p1, p2
    st.rerun()


# ------------------------------------------------------------------ LEADERBOARD / PROFILE / ACHIEVEMENTS
def screen_leaderboard():
    st.markdown("## 🏆 Global Leaderboard")
    rows = db.get_leaderboard(20)
    if not rows:
        st.info("No players yet — play a match!")
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        st.markdown(f"**{medal} {r['name']}** — Rating {r['rating']} · Level {r['level']} · "
                    f"{r['matches_won']}/{r['matches_played']} wins")
    if st.button("⬅️ Back"):
        st.session_state.screen = "home"; st.rerun()


def screen_profile():
    st.markdown("## 👤 Player Profile")
    name = st.selectbox("Player", [r["name"] for r in db.get_leaderboard(50)] or [st.session_state.player1_name])
    row = db.get_player(name)
    if row:
        win_rate = round(100 * row["matches_won"] / row["matches_played"], 1) if row["matches_played"] else 0.0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rating", row["rating"])
        c2.metric("Level", row["level"])
        c3.metric("XP", row["xp"])
        c4.metric("Win Rate", f"{win_rate}%")
        st.caption(f"🔥 Best streak: {row['best_streak']} · {row['matches_won']}/{row['matches_played']} matches won")
        render_skill_radar(name, f"{name}'s Skills")

        earned = db.get_achievements(name)
        if earned:
            st.markdown("### 🏅 Achievements")
            st.write(" ".join(ACHIEVEMENTS[a]["name"] for a in earned if a in ACHIEVEMENTS))
    if st.button("⬅️ Back"):
        st.session_state.screen = "home"; st.rerun()


def screen_achievements():
    st.markdown("## 🏅 All Achievements")
    for aid, a in ACHIEVEMENTS.items():
        st.write(f"**{a['name']}** — {a['desc']}")
    if st.button("⬅️ Back"):
        st.session_state.screen = "home"; st.rerun()


def screen_daily():
    st.markdown("## 🌅 Daily Code Challenge")
    seed = int(date.today().strftime("%Y%m%d"))
    rng = random.Random(seed)
    q = rng.choice(QUESTIONS)
    st.caption(f"Today's challenge · {date.today().isoformat()}")
    st.markdown(f"<span class='category-tag'>{q['category'].replace('_',' ').title()}</span>"
                f"<span class='difficulty-tag diff-{q['difficulty']}'>{q['difficulty']}</span>",
                unsafe_allow_html=True)
    st.markdown(f"<div class='question-box'><div class='question-text'>{q['question']}</div></div>",
                unsafe_allow_html=True)
    if q.get("code"):
        st.code(q["code"], language="python")

    options = options_for_display(q)
    choice = st.radio("Your answer", options, index=None)
    if st.button("Submit", type="primary"):
        idx = options.index(choice) if choice is not None else None
        correct = is_correct(q, idx, None)
        if correct:
            st.success("✅ Correct! +100 XP, +25 Rating")
            name = st.session_state.player1_name.strip() or "Player 1"
            db.ensure_player(name)
            db.update_player_after_match(name, 25, 100, True, 0)
        else:
            st.error(f"❌ Not quite. {q['explanation']}")
    if st.button("⬅️ Back"):
        st.session_state.screen = "home"; st.rerun()


# ------------------------------------------------------------------ SIDEBAR + ROUTER
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.session_state.api_key = st.text_input("Anthropic API key (optional, enables AI features)",
                                               value=st.session_state.api_key, type="password")
    st.caption("Without a key, the game runs entirely on the 60+ curated local questions.")
    st.divider()
    st.caption("⚔️ Code Battle AI — a competitive programming game")

screen = st.session_state.screen
if screen == "home":
    screen_home()
elif screen == "arena":
    screen_arena()
elif screen == "leaderboard":
    screen_leaderboard()
elif screen == "profile":
    screen_profile()
elif screen == "achievements":
    screen_achievements()
elif screen == "daily":
    screen_daily()
