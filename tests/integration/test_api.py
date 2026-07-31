from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import evaluation_controller
from app.main import app
from app.schemas.evaluation_schema import EvaluationResponse


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check_returns_application_metadata(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "access-fit-ai-test",
        "version": "test-version",
        "environment": "test",
    }


def test_single_evaluation_returns_service_response(
    client,
    monkeypatch,
    request_payload,
    response_payload,
):
    service = Mock()
    service.evaluate.return_value = EvaluationResponse(**response_payload)
    monkeypatch.setattr(evaluation_controller, "evaluation_service", service)

    response = client.post("/api/v1/evaluations", json=request_payload)

    assert response.status_code == 200
    assert response.json() == response_payload
    request = service.evaluate.call_args.args[0]
    assert request.tool_name == "GitHub Copilot"


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_detail"),
    [
        (
            ValueError("resposta inválida"),
            422,
            "resposta inválida",
        ),
        (
            RuntimeError("provedor indisponível"),
            503,
            "provedor indisponível",
        ),
        (
            Exception("falha inesperada"),
            500,
            "Erro interno ao processar a avaliação.",
        ),
    ],
)
def test_single_evaluation_maps_service_errors(
    client,
    monkeypatch,
    request_payload,
    error,
    expected_status,
    expected_detail,
):
    service = Mock()
    service.evaluate.side_effect = error
    monkeypatch.setattr(evaluation_controller, "evaluation_service", service)

    response = client.post("/api/v1/evaluations", json=request_payload)

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}


@pytest.mark.parametrize(
    "payload",
    [
        {
            "role": "X",
            "tool_name": "GitHub Copilot",
            "tool_type": "IA",
        },
        {
            "role": "Desenvolvedor",
            "tool_name": "GitHub Copilot",
            "tool_type": "DESCONHECIDO",
        },
    ],
)
def test_single_evaluation_rejects_invalid_request(client, payload):
    response = client.post("/api/v1/evaluations", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]


def test_batch_evaluation_rejects_empty_list(client):
    response = client.post("/api/v1/evaluations/batch", json=[])

    assert response.status_code == 400
    assert response.json() == {
        "detail": "A lista de avaliações não pode estar vazia."
    }


def test_batch_evaluation_rejects_more_than_fifty_items(client, request_payload):
    response = client.post(
        "/api/v1/evaluations/batch",
        json=[request_payload] * 51,
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "O lote não pode conter mais de 50 avaliações por requisição."
    }


def test_batch_evaluation_returns_all_results(
    client,
    monkeypatch,
    request_payload,
    response_payload,
):
    service = Mock()
    service.evaluate_batch.return_value = [
        EvaluationResponse(**response_payload),
        EvaluationResponse(**response_payload),
    ]
    monkeypatch.setattr(evaluation_controller, "evaluation_service", service)

    response = client.post(
        "/api/v1/evaluations/batch",
        json=[request_payload, request_payload],
    )

    assert response.status_code == 200
    assert response.json() == [response_payload, response_payload]
    assert len(service.evaluate_batch.call_args.args[0]) == 2


def test_batch_evaluation_converts_unexpected_error_to_500(
    client,
    monkeypatch,
    request_payload,
):
    service = Mock()
    service.evaluate_batch.side_effect = Exception("falha inesperada")
    monkeypatch.setattr(evaluation_controller, "evaluation_service", service)

    response = client.post(
        "/api/v1/evaluations/batch",
        json=[request_payload],
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Erro interno ao processar o lote de avaliações."
    }
