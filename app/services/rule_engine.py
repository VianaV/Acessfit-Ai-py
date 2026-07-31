"""
app/services/rule_engine.py
-----------------------------
Motor de regras para análise preliminar antes da chamada à IA.

A RuleEngine aplica heurísticas rápidas e determinísticas para:
1. Gerar contexto adicional que enriquece o prompt da IA.
2. Sinalizar casos óbvios de alto/baixo risco.
3. Tornar a avaliação mais precisa sem depender 100% da IA.

A RuleEngine NÃO toma a decisão final — ela apenas orienta a IA.
Isso mantém flexibilidade e evita falsos negativos por regras rígidas.
"""

from app.schemas.evaluation_schema import EvaluationRequest, ToolTypeEnum
from app.infra.logging_config import get_logger

logger = get_logger(__name__)


class RuleEngine:
    """
    Motor de regras da aplicação.

    Analisa o request e produz um texto de contexto
    a ser incluído no prompt da IA para enriquecer a avaliação.

    Regras aplicadas:
    - Aderência por tipo de ferramenta + cargo.
    - Sinais de risco a partir do contexto de negócio.
    - Alertas para cargos sem relação clara com a ferramenta.
    """

    # -------------------------------------------------------
    # Palavras-chave por domínio
    # -------------------------------------------------------

    # Cargos/áreas tipicamente beneficiados por ferramentas de IA
    AI_FAVORABLE_ROLES = [
        "desenvolvedor", "developer", "engenheiro", "engineer",
        "dados", "data", "analytics", "cientista", "scientist",
        "produto", "product", "tech", "tecnologia", "software",
        "arquiteto", "devops", "sre", "qa", "qualidade",
        "ia", "ml", "machine learning", "inteligência artificial",
        "pesquisa", "research", "inovação", "innovation",
    ]

    # Palavras que sinalizam risco elevado de exposição de dados
    HIGH_RISK_KEYWORDS = [
        "sensível", "confidencial", "lgpd", "gdpr", "pii",
        "credencial", "senha", "password", "token", "api key",
        "produção", "production", "cliente", "customer", "financeiro",
        "financeira", "contrato", "juridico", "jurídico", "saúde",
        "médico", "médica", "cpf", "cnpj", "rg", "passaporte",
    ]

    # Palavras que indicam maior necessidade da ferramenta
    HIGH_NECESSITY_KEYWORDS = [
        "produtividade", "automação", "eficiência", "agilidade",
        "diário", "frequente", "rotina", "principal", "essencial",
        "necessário", "obrigatório", "core", "fundamental",
    ]

    def analyze(self, request: EvaluationRequest) -> str:
        """
        Executa todas as regras e retorna um texto de contexto para a IA.

        Args:
            request: Dados validados do request.

        Returns:
            String com as observações e alertas identificados pelas regras.
            Será incorporada ao prompt enviado à IA.
        """
        observations = []

        # --- Regra 1: Aderência por tipo de ferramenta ---
        role_lower = request.role.lower()
        dept_lower = (request.department or "").lower()

        if request.tool_type == ToolTypeEnum.IA:
            if any(kw in role_lower or kw in dept_lower for kw in self.AI_FAVORABLE_ROLES):
                observations.append(
                    "✅ O cargo/departamento tem forte aderência ao uso de ferramentas de IA. "
                    "Isso aumenta a probabilidade de ganho real de produtividade."
                )
            else:
                observations.append(
                    "⚠️ O cargo/departamento não apresenta aderência clara ao uso de ferramentas de IA. "
                    "Avalie com cuidado se o uso será efetivo e necessário."
                )

        elif request.tool_type == ToolTypeEnum.SAAS:
            # Para SaaS, é mais difícil inferir aderência sem conhecer a ferramenta específica
            observations.append(
                "ℹ️ Ferramenta do tipo SaaS. Verifique se o cargo tem relação direta "
                "com o propósito da ferramenta para determinar a necessidade real."
            )

        # --- Regra 2: Risco de exposição de dados ---
        context_lower = (request.business_context or "").lower()
        role_and_context = role_lower + " " + context_lower

        detected_risk_keywords = [
            kw for kw in self.HIGH_RISK_KEYWORDS if kw in role_and_context
        ]

        if detected_risk_keywords:
            observations.append(
                f"🚨 ALERTA DE RISCO: Foram identificadas palavras associadas a dados sensíveis: "
                f"{', '.join(detected_risk_keywords)}. "
                f"Avalie cuidadosamente o risco de exposição de dados antes de aprovar o acesso."
            )
        else:
            observations.append(
                "✅ Nenhum sinal explícito de dados sensíveis identificado no contexto fornecido."
            )

        # --- Regra 3: Necessidade real da ferramenta ---
        detected_necessity = [
            kw for kw in self.HIGH_NECESSITY_KEYWORDS if kw in context_lower
        ]

        if detected_necessity:
            observations.append(
                f"✅ O contexto de negócio menciona indicadores de necessidade real: "
                f"{', '.join(detected_necessity)}. Isso justifica o acesso."
            )
        elif request.business_context:
            observations.append(
                "ℹ️ Contexto de negócio fornecido, mas sem indicadores claros de necessidade urgente."
            )
        else:
            observations.append(
                "⚠️ Nenhum contexto de negócio foi fornecido. "
                "A necessidade real da ferramenta para essa função não pôde ser verificada."
            )

        # --- Regra 4: Ferramenta de IA para cargo não-técnico ---
        if request.tool_type == ToolTypeEnum.IA and not any(
            kw in role_lower for kw in self.AI_FAVORABLE_ROLES
        ):
            observations.append(
                "⚠️ Cargos sem perfil técnico usando ferramentas de IA podem gerar uso inadequado. "
                "Considere se há necessidade de treinamento ou política de uso antes de liberar."
            )

        context_text = "\n".join(observations)
        logger.debug(f"RuleEngine gerou {len(observations)} observações.")
        return context_text
