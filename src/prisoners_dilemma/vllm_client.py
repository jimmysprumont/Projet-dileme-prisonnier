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


def fallback_decision(memory: PlayerMemory) -> AIDecision:
    if memory.last is None:
        choice = Choice.COOPERATE
        reasoning = "Fallback tit-for-tat starts with cooperation."
    else:
        choice = memory.last.opponent_choice
        reasoning = "Fallback tit-for-tat copied the opponent previous choice."
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
        except (KeyError, IndexError, TypeError, requests.RequestException, ValueError):
            return fallback_decision(memory)

        decision = parse_ai_decision(str(content))
        if decision is None:
            return fallback_decision(memory)
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

        user_prompt = {
            "profile_name": profile_name,
            "profile": profile_prompt,
            "round_index": round_index,
            "last_my_choices": recent_mine,
            "last_opponent_choices": recent_opponent,
            "my_score": my_score,
            "opponent_score": opponent_score,
            "instruction": "Return only JSON with keys choice and reasoning. choice must be C or D.",
        }

        return {
            "model": self.model,
            "temperature": 0.2,
            "max_tokens": 80,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You play the iterative prisoners dilemma. "
                        "Choose C to cooperate or D to defect. Return strict JSON only."
                    ),
                },
                {"role": "user", "content": json.dumps(user_prompt)},
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
