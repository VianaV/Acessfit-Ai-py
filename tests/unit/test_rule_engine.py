from app.schemas.evaluation_schema import EvaluationRequest
from app.services.rule_engine import RuleEngine


def test_ai_technical_role_with_clear_necessity_has_positive_signals(request_payload):
    request = EvaluationRequest(**request_payload)

    result = RuleEngine().analyze(request)

    assert "forte aderência" in result
    assert "Nenhum sinal explícito de dados sensíveis" in result
    assert "indicadores de necessidade real" in result
    assert "Cargos sem perfil técnico" not in result


def test_ai_non_technical_role_with_sensitive_context_has_warnings():
    request = EvaluationRequest(
        role="Assistente Administrativo",
        department="Operações",
        tool_name="ChatGPT",
        tool_type="IA",
        business_context="Consultar CPF de cliente em contrato confidencial.",
    )

    result = RuleEngine().analyze(request)

    assert "não apresenta aderência clara" in result
    assert "ALERTA DE RISCO" in result
    assert "confidencial" in result
    assert "cpf" in result
    assert "cliente" in result
    assert "sem indicadores claros de necessidade urgente" in result
    assert "Cargos sem perfil técnico" in result


def test_department_can_make_ai_request_favorable():
    request = EvaluationRequest(
        role="Analista",
        department="Data Analytics",
        tool_name="ChatGPT",
        tool_type="IA",
    )

    result = RuleEngine().analyze(request)

    assert "forte aderência" in result
    assert "Nenhum contexto de negócio foi fornecido" in result
    assert "Cargos sem perfil técnico" in result


def test_saas_without_business_context_uses_generic_analysis():
    request = EvaluationRequest(
        role="Analista Financeiro",
        tool_name="Jira",
        tool_type="SAAS",
    )

    result = RuleEngine().analyze(request)

    assert "Ferramenta do tipo SaaS" in result
    assert "ALERTA DE RISCO" in result
    assert "financeiro" in result
    assert "Nenhum contexto de negócio foi fornecido" in result
    assert "Cargos sem perfil técnico" not in result
