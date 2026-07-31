import os

import pytest


# As variáveis são definidas antes da coleta dos módulos da aplicação.
# Isso impede que os testes dependam do .env local ou de uma chave real.
os.environ["APP_ENV"] = "test"
os.environ["OPENAI_API_KEY"] = "test-api-key"
os.environ["OPENAI_MODEL"] = "test-model"
os.environ["APP_NAME"] = "access-fit-ai-test"
os.environ["APP_VERSION"] = "test-version"

# Impede que a inicialização local do SDK tente configurar um proxy ou rede.
for proxy_variable in (
    "ALL_PROXY",
    "all_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "HTTPS_PROXY",
    "https_proxy",
):
    os.environ.pop(proxy_variable, None)


@pytest.fixture
def request_payload() -> dict:
    return {
        "person_name": "João Silva",
        "role": "Desenvolvedor Backend",
        "department": "Tecnologia",
        "tool_name": "GitHub Copilot",
        "tool_type": "IA",
        "business_context": "Uso diário para produtividade e automação.",
    }


@pytest.fixture
def response_payload() -> dict:
    return {
        "decision": "RECOMENDADO",
        "score": 85,
        "risk_level": "MEDIO",
        "justification": "A ferramenta possui forte aderência ao cargo.",
        "recommended_access": "Acesso padrão com política de uso.",
        "main_use_cases": ["Apoio em desenvolvimento", "Geração de testes"],
        "conditions": ["Não inserir credenciais ou dados sensíveis."],
        "provider": "openai",
        "model": "test-model",
    }
