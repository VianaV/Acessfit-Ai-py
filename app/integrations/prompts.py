"""
app/integrations/prompts.py
-----------------------------
Centraliza todos os prompts enviados para os modelos de IA.

Manter prompts separados do código de integração (openai_client.py)
e do serviço (evaluation_service.py) garante:
- Fácil manutenção e ajuste de prompts sem tocar na lógica.
- Versionamento claro de prompts.
- Reutilização de prompts em diferentes providers.
"""

from app.schemas.evaluation_schema import EvaluationRequest


# -------------------------------------------------------
# System Prompt
# -------------------------------------------------------

SYSTEM_PROMPT = """Você é um analista sênior de governança de acessos e segurança da informação.

Sua função é avaliar se uma pessoa, com determinado cargo e departamento, deve ou não ter acesso a uma ferramenta do tipo IA ou SaaS.

Você deve considerar obrigatoriamente:
1. **Aderência ao cargo**: O cargo da pessoa está alinhado com o propósito da ferramenta?
2. **Ganho de produtividade**: A ferramenta trará ganho real de produtividade para essa função?
3. **Risco de segurança**: Existe risco de vazamento de dados sensíveis, credenciais ou informações confidenciais?
4. **Exposição de dados**: A ferramenta processa dados que poderiam ser expostos externamente (ex: dados de clientes, propriedade intelectual, PII)?
5. **Necessidade real**: O uso da ferramenta é necessário para a função ou seria apenas conveniência?
6. **Ferramentas alternativas**: Existem outras ferramentas já disponíveis que poderiam atender à necessidade?

Regras de decisão:
- Score 70-100: RECOMENDADO
- Score 40-69: ANALISE_HUMANA
- Score 0-39: NAO_RECOMENDADO

Risco:
- BAIXO: ferramenta não processa dados sensíveis, uso controlado.
- MEDIO: ferramenta pode processar dados moderadamente sensíveis.
- ALTO: ferramenta tem acesso a dados críticos, PII, credenciais ou propriedade intelectual.

Responda SOMENTE com um JSON válido, sem texto adicional, sem markdown, sem explicações fora do JSON.
O JSON deve seguir exatamente o schema solicitado."""


# -------------------------------------------------------
# Função de construção do User Prompt
# -------------------------------------------------------

def build_evaluation_prompt(request: EvaluationRequest, rule_context: str) -> str:
    """
    Constrói o prompt de usuário para a avaliação de acesso.

    Combina os dados do request com o contexto gerado pela RuleEngine
    para dar mais informações à IA antes de decidir.

    Args:
        request: Dados validados do request (EvaluationRequest).
        rule_context: Texto gerado pela RuleEngine com observações preliminares.

    Returns:
        String formatada pronta para ser enviada como mensagem do usuário à IA.
    """

    # Monta bloco de dados da pessoa e da ferramenta
    person_info = f"""
DADOS DA AVALIAÇÃO:
-------------------
Pessoa: {request.person_name or "Não informado"}
Cargo: {request.role}
Departamento: {request.department or "Não informado"}
Ferramenta: {request.tool_name}
Tipo da Ferramenta: {request.tool_type.value}
Contexto de Negócio: {request.business_context or "Não informado"}
"""

    # Bloco com observações preliminares da RuleEngine
    rule_block = f"""
ANÁLISE PRELIMINAR (Rule Engine):
----------------------------------
{rule_context}
"""

    # Schema exato que a IA deve retornar
    schema_block = """
SCHEMA DE RESPOSTA OBRIGATÓRIO (JSON puro, sem markdown):
----------------------------------------------------------
{
  "decision": "RECOMENDADO" | "NAO_RECOMENDADO" | "ANALISE_HUMANA",
  "score": <inteiro de 0 a 100>,
  "risk_level": "BAIXO" | "MEDIO" | "ALTO",
  "justification": "<justificativa clara e objetiva em português>",
  "recommended_access": "<descrição do tipo de acesso recomendado>",
  "main_use_cases": ["<caso de uso 1>", "<caso de uso 2>", "..."],
  "conditions": ["<condição ou restrição 1>", "<condição 2>", "..."]
}
"""

    return person_info + rule_block + schema_block
