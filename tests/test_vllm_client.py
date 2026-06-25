import requests

from prisoners_dilemma.domain import Choice, PlayerMemory, RoundObservation
from prisoners_dilemma.vllm_client import (
    AIDecision,
    VLLMClient,
    fallback_decision,
    parse_ai_decision,
)


def memory_after_opponent_defected() -> PlayerMemory:
    return PlayerMemory(
        [
            RoundObservation(
                round_index=1,
                my_choice=Choice.COOPERATE,
                opponent_choice=Choice.DEFECT,
                my_payoff=0,
                opponent_payoff=5,
                my_cumulative_score=0,
                opponent_cumulative_score=5,
            )
        ]
    )


def test_parse_ai_decision_reads_strict_json_object() -> None:
    decision = parse_ai_decision('{"choice": "D", "reasoning": "Opponent defected."}')

    assert decision == AIDecision(
        choice=Choice.DEFECT,
        reasoning="Opponent defected.",
        source="vllm",
    )


def test_parse_ai_decision_extracts_json_from_markdown() -> None:
    decision = parse_ai_decision(
        '```json\n{"choice": "C", "reasoning": "Mutual cooperation is best."}\n```'
    )

    assert decision.choice is Choice.COOPERATE
    assert decision.reasoning == "Mutual cooperation is best."
    assert decision.source == "vllm"


def test_parse_ai_decision_accepts_single_token_choice() -> None:
    decision = parse_ai_decision("C to")

    assert decision == AIDecision(
        choice=Choice.COOPERATE,
        reasoning="vLLM selected cooperation.",
        source="vllm",
    )


def test_parse_ai_decision_rejects_invalid_choice() -> None:
    decision = parse_ai_decision('{"choice": "WAIT", "reasoning": "No"}')

    assert decision is None


def test_fallback_decision_uses_tit_for_tat() -> None:
    assert fallback_decision(PlayerMemory()).choice is Choice.COOPERATE
    assert fallback_decision(memory_after_opponent_defected()).choice is Choice.DEFECT
    assert fallback_decision(PlayerMemory()).source == "fallback"


def test_vllm_client_returns_fallback_when_request_fails(monkeypatch) -> None:
    class FailingSession:
        def post(self, *args, **kwargs):
            raise requests.RequestException("offline")

    client = VLLMClient(
        base_url="http://127.0.0.1:8000/v1",
        model="local-model",
        session=FailingSession(),
    )

    decision = client.decide(
        profile_name="empathic_ai",
        profile_prompt="Prefer cooperation.",
        memory=memory_after_opponent_defected(),
    )

    assert decision.choice is Choice.DEFECT
    assert decision.source == "fallback"
    assert "vLLM request failed" in decision.reasoning


def test_vllm_client_uses_compact_cpu_friendly_payload() -> None:
    client = VLLMClient(
        base_url="http://127.0.0.1:8000/v1",
        model="local-model",
    )

    payload = client._payload(
        profile_name="empathic_ai",
        profile_prompt="Prefer cooperation.",
        memory=memory_after_opponent_defected(),
    )

    assert payload["temperature"] == 0
    assert payload["max_tokens"] == 1
    assert len(payload["messages"]) == 1
    assert "exactly one letter" in payload["messages"][0]["content"]


def test_vllm_client_returns_model_decision(monkeypatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"choice": "C", "reasoning": "I forgive once."}'
                        }
                    }
                ]
            }

    class WorkingSession:
        def post(self, *args, **kwargs):
            return Response()

    client = VLLMClient(
        base_url="http://127.0.0.1:8000/v1",
        model="local-model",
        session=WorkingSession(),
    )

    decision = client.decide(
        profile_name="empathic_ai",
        profile_prompt="Prefer cooperation.",
        memory=memory_after_opponent_defected(),
    )

    assert decision == AIDecision(
        choice=Choice.COOPERATE,
        reasoning="I forgive once.",
        source="vllm",
    )
