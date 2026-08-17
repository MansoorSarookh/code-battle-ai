"""
AI question generation, hints, explanations and post-match coaching.

Architecture (matches the design doc's 'AI should NOT control everything'
principle): AI -> generate_question() -> strict JSON schema validation ->
answer/safety validation -> only THEN does it reach the question database /
game engine. Anything that fails validation is silently discarded and the
game falls back to the curated local bank (data/questions_bank.py) — a
player should never be able to tell whether a given round was AI-generated
or hand-written.

Nothing in this module is called unless the user supplies their own
Anthropic API key in the sidebar; the whole game is fully playable without it.
"""
from __future__ import annotations

import json
import re
from typing import Optional

try:
    import anthropic
except ImportError:  # library optional until AI features are actually used
    anthropic = None

MODEL = "claude-sonnet-4-5"

_BANNED_PATTERNS = [
    r"\bos\.system\b", r"\bsubprocess\b", r"\beval\(", r"\bexec\(",
    r"\b__import__\b", r"\bopen\(", r"rm\s+-rf", r"\bsocket\b",
]


def _client(api_key: str):
    if anthropic is None:
        raise RuntimeError("The `anthropic` package is not installed. Run: pip install anthropic")
    return anthropic.Anthropic(api_key=api_key)


def _safety_check(text: str) -> bool:
    return not any(re.search(p, text, re.IGNORECASE) for p in _BANNED_PATTERNS)


def _extract_json(text: str) -> Optional[dict]:
    text = text.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _validate_generated_question(data: dict) -> bool:
    required = {"category", "difficulty", "type", "question", "options", "correct_answer", "explanation"}
    if not required.issubset(data.keys()):
        return False
    if data["difficulty"] not in {"Easy", "Medium", "Hard", "Expert"}:
        return False
    if not isinstance(data["options"], list) or not (2 <= len(data["options"]) <= 4):
        return False
    if not isinstance(data["correct_answer"], int) or not (0 <= data["correct_answer"] < len(data["options"])):
        return False
    blob = json.dumps(data)
    if not _safety_check(blob):
        return False
    if len(data["question"]) > 600 or len(data["explanation"]) > 600:
        return False
    return True


def generate_question(api_key: str, language: str, topic: str, difficulty: str, question_type: str = "output_prediction") -> Optional[dict]:
    """Returns a validated question dict in the same shape as the local bank, or None on any failure."""
    if not api_key:
        return None
    prompt = f"""Generate ONE programming quiz question as strict JSON, nothing else — no markdown fences, no preamble.

Schema:
{{
  "category": string (short slug, e.g. "loops_control"),
  "difficulty": "Easy" | "Medium" | "Hard" | "Expert",
  "type": "mcq" | "output" | "debugging" | "complexity",
  "question": string,
  "code": string or null (a short code snippet if relevant),
  "options": array of 2-4 short strings,
  "correct_answer": integer index into options,
  "explanation": string (1-2 sentences, why the answer is correct)
}}

Constraints: language={language}, topic={topic}, difficulty={difficulty}, question_type={question_type}.
The question must have exactly one unambiguous correct answer. Keep code snippets under 8 lines.
Do not include any instructions to execute shell commands, file I/O, or network calls in the code snippet."""

    try:
        client = _client(api_key)
        resp = client.messages.create(
            model=MODEL, max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        data = _extract_json(text)
        if data is None or not _validate_generated_question(data):
            return None
        return {
            "id": f"ai_{abs(hash(data['question'])) % 100000}",
            "category": data["category"],
            "difficulty": data["difficulty"],
            "type": data["type"] if data["type"] in {"mcq", "output", "debugging", "complexity"} else "mcq",
            "question": data["question"],
            "code": data.get("code"),
            "options": data["options"],
            "correct": data["correct_answer"],
            "explanation": data["explanation"],
            "time_limit": {"Easy": 15, "Medium": 20, "Hard": 25, "Expert": 30}[data["difficulty"]],
            "ai_generated": True,
        }
    except Exception:
        return None


def generate_hint(api_key: str, question: dict, hint_level: int) -> Optional[str]:
    if not api_key:
        return None
    try:
        client = _client(api_key)
        prompt = (
            f"A player is stuck on this quiz question and wants hint level {hint_level} "
            f"(1=vague nudge, 2=strong hint, never reveal the final answer letter/index).\n\n"
            f"Question: {question['question']}\nCode: {question.get('code', 'N/A')}\n"
            f"Options: {question['options']}\n\n"
            f"Give ONE short hint sentence, nothing else."
        )
        resp = client.messages.create(model=MODEL, max_tokens=120, messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
        return text if _safety_check(text) else None
    except Exception:
        return None


def generate_coach_report(api_key: str, player: str, skills: dict, won: bool) -> Optional[str]:
    """skills: {category: {correct, total, accuracy}} from database.get_skill_breakdown"""
    if not api_key or not skills:
        return None
    try:
        client = _client(api_key)
        prompt = (
            f"You are an AI coding coach. Player '{player}' just {'won' if won else 'lost'} a match. "
            f"Their per-category accuracy is: {json.dumps(skills)}.\n"
            f"Write a short (3-4 sentence) coach report: 1) name their 1-2 strongest categories, "
            f"2) name their 1-2 weakest categories, 3) give ONE concrete practice recommendation. "
            f"Be encouraging but specific. Plain text, no markdown headers."
        )
        resp = client.messages.create(model=MODEL, max_tokens=300, messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
        return text if _safety_check(text) else None
    except Exception:
        return None
