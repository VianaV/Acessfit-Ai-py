import pytest
from pydantic import ValidationError

from app.schemas.evaluation_schema import (
    DecisionEnum,
    EvaluationRequest,
    EvaluationResponse,
    RiskLevelEnum,
    ToolTypeEnum,
)


def test_evaluation_request_accepts_valid_payload(request_payload):
    request = EvaluationRequest(**request_payload)

    assert request.person_name == "João Silva"
    assert request.role == "Desenvolvedor Backend"
    assert request.department == "Tecnologia"
    assert request.tool_name == "GitHub Copilot"
    assert request.tool_type is ToolTypeEnum.IA
    assert request.business_context == "Uso diário para produtividade e automação."


def test_evaluation_request_applies_optional_defaults():
    request = EvaluationRequest(
        role="QA",
        tool_name="Jira",
        tool_type=ToolTypeEnum.SAAS,
    )

    assert request.person_name is None
    assert request.department is None
    assert request.business_context is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("role", "X"),
        ("role", "X" * 201),
        ("tool_name", "X"),
        ("tool_name", "X" * 201),
        ("department", "X" * 201),
        ("business_context", "X" * 1001),
        ("tool_type", "OUTRO"),
    ],
)
def test_evaluation_request_rejects_invalid_fields(request_payload, field, value):
    request_payload[field] = value

    with pytest.raises(ValidationError):
        EvaluationRequest(**request_payload)


def test_evaluation_response_accepts_valid_payload(response_payload):
    response = EvaluationResponse(**response_payload)

    assert response.decision is DecisionEnum.RECOMENDADO
    assert response.risk_level is RiskLevelEnum.MEDIO
    assert response.score == 85


def test_evaluation_response_creates_independent_empty_lists(response_payload):
    response_payload.pop("main_use_cases")
    response_payload.pop("conditions")

    first = EvaluationResponse(**response_payload)
    second = EvaluationResponse(**response_payload)
    first.main_use_cases.append("Novo caso")

    assert second.main_use_cases == []
    assert first.conditions == []


@pytest.mark.parametrize("score", [-1, 101])
def test_evaluation_response_rejects_score_outside_range(response_payload, score):
    response_payload["score"] = score

    with pytest.raises(ValidationError):
        EvaluationResponse(**response_payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("decision", "APROVADO"),
        ("risk_level", "CRITICO"),
    ],
)
def test_evaluation_response_rejects_invalid_enums(response_payload, field, value):
    response_payload[field] = value

    with pytest.raises(ValidationError):
        EvaluationResponse(**response_payload)
