from unittest.mock import Mock

import pytest

from app.integrations.prompts import SYSTEM_PROMPT
from app.schemas.evaluation_schema import (
    DecisionEnum,
    EvaluationRequest,
    RiskLevelEnum,
)
from app.services.evaluation_service import EvaluationService


def make_service(rule_context="contexto de regras", ai_result=None):
    service = EvaluationService.__new__(EvaluationService)
    service.rule_engine = Mock()
    service.rule_engine.analyze.return_value = rule_context
    service.ai_client = Mock()
    service.ai_client.evaluate.return_value = ai_result
    return service


def test_constructor_creates_default_dependencies(monkeypatch):
    rule_engine = object()
    ai_client = object()
    monkeypatch.setattr(
        "app.services.evaluation_service.RuleEngine",
        Mock(return_value=rule_engine),
    )
    monkeypatch.setattr(
        "app.services.evaluation_service.OpenAIClient",
        Mock(return_value=ai_client),
    )

    service = EvaluationService()

    assert service.rule_engine is rule_engine
    assert service.ai_client is ai_client


def test_evaluate_orchestrates_rules_prompt_ai_and_validation(
    request_payload,
    response_payload,
):
    request = EvaluationRequest(**request_payload)
    service = make_service(ai_result=response_payload)

    response = service.evaluate(request)

    service.rule_engine.analyze.assert_called_once_with(request)
    call = service.ai_client.evaluate.call_args.kwargs
    assert call["system_prompt"] == SYSTEM_PROMPT
    assert "contexto de regras" in call["user_prompt"]
    assert "GitHub Copilot" in call["user_prompt"]
    assert response.decision is DecisionEnum.RECOMENDADO
    assert response.score == 85


def test_evaluate_uses_role_as_log_label_when_name_is_missing(response_payload):
    request = EvaluationRequest(role="QA", tool_name="Jira", tool_type="SAAS")
    service = make_service(ai_result=response_payload)

    response = service.evaluate(request)

    assert response.score == 85


def test_evaluate_converts_invalid_ai_payload_to_value_error(request_payload):
    request = EvaluationRequest(**request_payload)
    service = make_service(ai_result={"decision": "INVALIDA"})

    with pytest.raises(ValueError, match="Resposta da IA inválida"):
        service.evaluate(request)


def test_evaluate_batch_keeps_success_and_builds_fallback(
    request_payload,
    response_payload,
):
    first = EvaluationRequest(**request_payload)
    request_payload["tool_name"] = "Ferramenta com falha"
    second = EvaluationRequest(**request_payload)
    service = make_service()
    successful_response = make_service(ai_result=response_payload).evaluate(first)
    service.evaluate = Mock(
        side_effect=[successful_response, RuntimeError("indisponível")]
    )

    results = service.evaluate_batch([first, second])

    assert results[0] is successful_response
    assert results[1].decision is DecisionEnum.ANALISE_HUMANA
    assert results[1].score == 0
    assert results[1].risk_level is RiskLevelEnum.ALTO
    assert "indisponível" in results[1].justification
    assert results[1].provider == "system"
    assert results[1].model == "fallback"
    assert service.evaluate.call_count == 2


def test_evaluate_batch_accepts_empty_internal_list():
    service = make_service()

    assert service.evaluate_batch([]) == []
