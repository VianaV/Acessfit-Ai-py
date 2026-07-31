import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import app.integrations.openai_client as openai_module
from app.integrations.openai_client import OpenAIClient


def make_client_with_create(create):
    client = OpenAIClient.__new__(OpenAIClient)
    client.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create),
        )
    )
    client.model = "test-model"
    return client


def make_openai_response(content):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


def test_constructor_uses_configured_key_and_model(monkeypatch):
    sdk_client = object()
    openai_factory = Mock(return_value=sdk_client)
    monkeypatch.setattr(openai_module, "OpenAI", openai_factory)
    monkeypatch.setattr(openai_module.settings, "OPENAI_API_KEY", "configured-key")
    monkeypatch.setattr(openai_module.settings, "OPENAI_MODEL", "configured-model")

    client = OpenAIClient()

    openai_factory.assert_called_once_with(api_key="configured-key")
    assert client.client is sdk_client
    assert client.model == "configured-model"


def test_evaluate_calls_chat_completion_and_adds_metadata():
    create = Mock(
        return_value=make_openai_response(
            json.dumps(
                {
                    "decision": "RECOMENDADO",
                    "score": 90,
                    "risk_level": "BAIXO",
                }
            )
        )
    )
    client = make_client_with_create(create)

    result = client.evaluate("prompt de sistema", "prompt de usuário")

    create.assert_called_once_with(
        model="test-model",
        messages=[
            {"role": "system", "content": "prompt de sistema"},
            {"role": "user", "content": "prompt de usuário"},
        ],
        temperature=0.2,
        max_tokens=1500,
        response_format={"type": "json_object"},
    )
    assert result["provider"] == "openai"
    assert result["model"] == "test-model"
    assert result["score"] == 90


def test_evaluate_converts_rate_limit_error(monkeypatch):
    class FakeRateLimitError(Exception):
        pass

    monkeypatch.setattr(openai_module, "RateLimitError", FakeRateLimitError)
    client = make_client_with_create(Mock(side_effect=FakeRateLimitError("quota")))

    with pytest.raises(RuntimeError, match="Limite de requisições"):
        client.evaluate("system", "user")


def test_evaluate_converts_timeout_error(monkeypatch):
    class FakeTimeoutError(Exception):
        pass

    monkeypatch.setattr(openai_module, "APITimeoutError", FakeTimeoutError)
    client = make_client_with_create(Mock(side_effect=FakeTimeoutError("timeout")))

    with pytest.raises(RuntimeError, match="excedeu o tempo limite"):
        client.evaluate("system", "user")


def test_evaluate_converts_invalid_json():
    client = make_client_with_create(
        Mock(return_value=make_openai_response("não é json"))
    )

    with pytest.raises(ValueError, match="formato inválido"):
        client.evaluate("system", "user")


def test_evaluate_converts_generic_openai_error(monkeypatch):
    class FakeOpenAIError(Exception):
        pass

    monkeypatch.setattr(openai_module, "OpenAIError", FakeOpenAIError)
    client = make_client_with_create(
        Mock(side_effect=FakeOpenAIError("serviço indisponível"))
    )

    with pytest.raises(RuntimeError, match="Erro ao chamar a OpenAI"):
        client.evaluate("system", "user")
