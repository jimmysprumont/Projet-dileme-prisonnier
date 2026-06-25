from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests

from prisoners_dilemma.domain import Choice, PlayerMemory


@dataclass(frozen=True)
class AIDecision:
    choice: Choice
    reasoning: str
    source: str


def parse_ai_decision(content: str) -> AIDecision | None:
    stripped = content.strip().upper()
    if stripped in {"C", "COOPERATE"} or stripped.startswith("C "):
        return AIDecision(
            choice=Choice.COOPERATE,
            reasoning="vLLM selected cooperation.",
            source="vllm",
        )
    if stripped in {"D", "DEFECT"} or stripped.startswith("D "):
        return AIDecision(
            choice=Choice.DEFECT,
            reasoning="vLLM selected defection.",
            source="vllm",
        )

    payload = _extract_json_object(content)
    if payload is None:
        return None

    try:
        raw = json.loads(payload)
        choice = Choice.from_token(str(raw["choice"]))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None

    reasoning = str(raw.get("reasoning", "")).strip()
    return AIDecision(choice=choice, reasoning=reasoning, source="vllm")


def fallback_decision(memory: PlayerMemory, reason: str | None = None) -> AIDecision:
    if memory.last is None:
        choice = Choice.COOPERATE
        reasoning = "Fallback tit-for-tat starts with cooperation."
    else:
        choice = memory.last.opponent_choice
        reasoning = "Fallback tit-for-tat copied the opponent previous choice."
    if reason:
        reasoning = f"{reason} {reasoning}"
    return AIDecision(choice=choice, reasoning=reasoning, source="fallback")


class VLLMClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: int = 20,
        history_window: int = 6,
        session: Any | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.history_window = history_window
        self.session = session or requests.Session()

    def decide(
        self,
        profile_name: str,
        profile_prompt: str,
        memory: PlayerMemory,
    ) -> AIDecision:
        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=self._payload(profile_name, profile_prompt, memory),
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        except requests.Timeout:
            return fallback_decision(memory, "vLLM request timed out.")
        except requests.RequestException as exc:
            return fallback_decision(memory, f"vLLM request failed: {exc.__class__.__name__}.")
        except (KeyError, IndexError, TypeError, ValueError):
            return fallback_decision(memory, "vLLM response was not OpenAI-compatible.")

        decision = parse_ai_decision(str(content))
        if decision is None:
            return fallback_decision(memory, "vLLM response was not valid decision JSON.")
        return decision

    def _payload(
        self,
        profile_name: str,
        profile_prompt: str,
        memory: PlayerMemory,
    ) -> dict[str, Any]:
        recent_mine = [choice.value for choice in memory.recent_my_choices(self.history_window)]
        recent_opponent = [
            choice.value for choice in memory.recent_opponent_choices(self.history_window)
        ]
        round_index = len(memory.observations) + 1
        my_score = memory.last.my_cumulative_score if memory.last else 0
        opponent_score = memory.last.opponent_cumulative_score if memory.last else 0

        goal = _compact_goal(profile_name, profile_prompt)
        user_prompt = (
            "You must output exactly one letter: C or D. No words. "
            f"Goal: {goal}. "
            f"Round {round_index}. My last {_format_choices(recent_mine)}. "
            f"Opponent last {_format_choices(recent_opponent)}. "
            f"Score {my_score}/{opponent_score}. Letter:"
        )

        return {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 1,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
        }


def _extract_json_object(content: str) -> str | None:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = [line for line in stripped.splitlines() if not line.strip().startswith("```")]
        stripped = "\n".join(lines).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    return stripped[start : end + 1]


def _compact_goal(profile_name: str, profile_prompt: str) -> str:
    if profile_name == "calculator_ai":
        return "maximize score"
    if profile_name == "empathic_ai":
        return "cooperate unless repeatedly exploited"
    return (
        profile_prompt.replace("You ", "")
        .replace("you ", "")
        .replace("your ", "")
        .strip()
    )


def _format_choices(choices: list[str]) -> str:
    return ",".join(choices) if choices else "none"
