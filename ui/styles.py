"""Dark 'coding arena' CSS theme + small HTML component helpers."""
from __future__ import annotations
import streamlit as st

ARENA_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Inter:wght@400;600;800&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
code, pre, .stCodeBlock, .stCode { font-family: 'JetBrains Mono', monospace !important; }

.stApp {
    background: radial-gradient(circle at 20% 0%, #151a2e 0%, #0a0c14 55%, #05060a 100%);
    color: #e6e8f0;
}

/* ---- player cards ---- */
.player-card {
    border-radius: 16px;
    padding: 18px 22px;
    text-align: center;
    font-weight: 800;
    box-shadow: 0 0 22px rgba(0,0,0,0.35);
    transition: transform 0.15s ease;
}
.player-card.red   { background: linear-gradient(145deg, #3a0d12, #1a0507); border: 1px solid #ff4d5e55; }
.player-card.blue  { background: linear-gradient(145deg, #06213a, #04101f); border: 1px solid #4dc3ff55; }
.player-name-red   { color: #ff5f6d; font-size: 1.15rem; letter-spacing: 0.5px; }
.player-name-blue  { color: #4dc3ff; font-size: 1.15rem; letter-spacing: 0.5px; }
.player-score { font-size: 2.1rem; font-weight: 800; margin-top: 4px; }
.player-rating { opacity: 0.65; font-size: 0.8rem; font-weight: 600; }

/* ---- round / timer header ---- */
.round-pill {
    text-align: center; font-weight: 800; letter-spacing: 2px;
    color: #b9bfd6; text-transform: uppercase; font-size: 0.85rem; margin-bottom: 4px;
}
.timer-badge {
    text-align: center; font-family: 'JetBrains Mono', monospace; font-weight: 800;
    font-size: 1.6rem; color: #ffd166;
    text-shadow: 0 0 18px rgba(255,209,102,0.55);
}
.timer-badge.low { color: #ff5f6d; text-shadow: 0 0 18px rgba(255,95,109,0.6); }

/* ---- question panel ---- */
.category-tag {
    display: inline-block; background: #6c5ce733; color: #b9a5ff; border: 1px solid #6c5ce755;
    padding: 3px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 700;
    letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 10px;
}
.difficulty-tag { display: inline-block; padding: 3px 12px; border-radius: 999px; font-size: 0.75rem;
    font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; margin-left: 8px; }
.diff-Easy    { background: #1fbf7533; color: #3ddc97; border: 1px solid #1fbf7555; }
.diff-Medium  { background: #ffd16633; color: #ffd166; border: 1px solid #ffd16655; }
.diff-Hard    { background: #ff8f4033; color: #ff9f5a; border: 1px solid #ff8f4055; }
.diff-Expert  { background: #ff4d5e33; color: #ff6b7a; border: 1px solid #ff4d5e55; }

.question-box {
    background: #0f1220; border: 1px solid #2a2f4a; border-radius: 14px;
    padding: 22px 26px; margin: 10px 0 18px 0;
    box-shadow: inset 0 0 30px rgba(108,92,231,0.06);
}
.question-text { font-size: 1.15rem; font-weight: 700; line-height: 1.5; color: #f1f2f9; }

/* ---- streak fire ---- */
.streak-banner {
    text-align: center; font-size: 1.1rem; font-weight: 800; color: #ff9f1c;
    animation: pulse 1.1s infinite;
}
@keyframes pulse { 0% {opacity:0.65;} 50% {opacity:1;} 100% {opacity:0.65;} }

/* ---- feedback flashes ---- */
.flash-correct {
    text-align:center; font-size:1.6rem; font-weight:900; color:#3ddc97;
    animation: pop 0.4s ease-out;
}
.flash-wrong {
    text-align:center; font-size:1.6rem; font-weight:900; color:#ff5f6d;
    animation: pop 0.4s ease-out;
}
@keyframes pop { 0% {transform: scale(0.6); opacity:0;} 70% {transform: scale(1.08);} 100% {transform: scale(1); opacity:1;} }

/* ---- victory ---- */
.victory-title {
    text-align:center; font-size: 2.4rem; font-weight: 900;
    background: linear-gradient(90deg, #ffd166, #ff9f5a, #ff5f6d);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    animation: pulse 1.6s infinite;
}

/* ---- handoff ---- */
.handoff-box {
    text-align:center; padding: 60px 20px; border: 2px dashed #6c5ce7aa; border-radius: 18px;
    background: #10122099;
}

/* buttons */
.stButton>button {
    border-radius: 10px !important; font-weight: 700 !important; border: 1px solid #2a2f4a !important;
}
</style>
"""


def inject_css() -> None:
    st.markdown(ARENA_CSS, unsafe_allow_html=True)


def player_card_html(name: str, score: int, rating: int | None, color: str) -> str:
    cls = "red" if color == "red" else "blue"
    name_cls = "player-name-red" if color == "red" else "player-name-blue"
    rating_html = f"<div class='player-rating'>Rating {rating}</div>" if rating is not None else ""
    return f"""
    <div class="player-card {cls}">
        <div class="{name_cls}">{'🔴' if color=='red' else '🔵'} {name}</div>
        <div class="player-score">{score}</div>
        {rating_html}
    </div>
    """


def timer_html(seconds_left: float) -> str:
    cls = "low" if seconds_left <= 5 else ""
    return f"<div class='timer-badge {cls}'>⏱️ {max(0, seconds_left):.0f}s</div>"


def play_sound(_event: str) -> None:
    """No-op hook — wire this to local mp3 assets + st.audio(..., autoplay=True) if desired."""
    return None
