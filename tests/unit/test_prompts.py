from app.integrations.prompts import SYSTEM_PROMPT, build_evaluation_prompt
from app.schemas.evaluation_schema import EvaluationRequest


def test_system_prompt_documents_decision_and_risk_rules():
    assert "Score 70-100: RECOMENDADO" in SYSTEM_PROMPT
    assert "Score 40-69: ANALISE_HUMANA" in SYSTEM_PROMPT
    assert "Score 0-39: NAO_RECOMENDADO" in SYSTEM_PROMPT
    assert "Responda SOMENTE com um JSON válido" in SYSTEM_PROMPT


def test_build_prompt_includes_request_rule_context_and_schema(request_payload):
    request = EvaluationRequest(**request_payload)

    prompt = build_evaluation_prompt(request, "Contexto determinístico de teste")

    assert "Pessoa: João Silva" in prompt
    assert "Cargo: Desenvolvedor Backend" in prompt
    assert "Departamento: Tecnologia" in prompt
    assert "Ferramenta: GitHub Copilot" in prompt
    assert "Tipo da Ferramenta: IA" in prompt
    assert "Uso diário para produtividade e automação." in prompt
    assert "Contexto determinístico de teste" in prompt
    assert '"decision": "RECOMENDADO"' in prompt


def test_build_prompt_marks_missing_optional_fields():
    request = EvaluationRequest(
        role="Analista",
        tool_name="Jira",
        tool_type="SAAS",
    )

    prompt = build_evaluation_prompt(request, "Sem alertas")

    assert "Pessoa: Não informado" in prompt
    assert "Departamento: Não informado" in prompt
    assert "Contexto de Negócio: Não informado" in prompt
