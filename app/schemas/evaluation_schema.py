"""
app/schemas/evaluation_schema.py
----------------------------------
Define os schemas (DTOs) de entrada e saída da API usando Pydantic.

Schemas são contratos entre o cliente e a API:
- Validam os dados recebidos (request).
- Garantem o formato correto dos dados enviados (response).
- Documentam automaticamente a API no Swagger (/docs).

Nenhuma lógica de negócio deve existir aqui — apenas estrutura e validação.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# -------------------------------------------------------
# Enumerações (valores permitidos)
# -------------------------------------------------------

class ToolTypeEnum(str, Enum):
    """
    Tipo da ferramenta sendo avaliada.
    Aceita apenas 'IA' ou 'SAAS'.
    Herdar de str permite serialização direta para JSON.
    """
    IA = "IA"
    SAAS = "SAAS"


class DecisionEnum(str, Enum):
    """
    Decisão final da avaliação.

    - RECOMENDADO: acesso aprovado pela análise.
    - NAO_RECOMENDADO: acesso negado pela análise.
    - ANALISE_HUMANA: caso ambíguo que requer revisão humana.
    """
    RECOMENDADO = "RECOMENDADO"
    NAO_RECOMENDADO = "NAO_RECOMENDADO"
    ANALISE_HUMANA = "ANALISE_HUMANA"


class RiskLevelEnum(str, Enum):
    """
    Nível de risco associado ao acesso à ferramenta.

    - BAIXO: pouco risco de segurança ou exposição de dados.
    - MEDIO: risco moderado, recomendada atenção.
    - ALTO: risco elevado, uso deve ser restrito ou monitorado.
    """
    BAIXO = "BAIXO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"


# -------------------------------------------------------
# Schema de Requisição (Request DTO)
# -------------------------------------------------------

class EvaluationRequest(BaseModel):
    """
    Dados enviados pelo cliente para solicitar uma avaliação de acesso.

    Campos obrigatórios: role, tool_name, tool_type.
    Campos opcionais: person_name, department, business_context.
    """

    person_name: Optional[str] = Field(
        default=None,
        description="Nome da pessoa sendo avaliada (opcional).",
        examples=["João Silva"],
    )

    role: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Cargo ou função da pessoa na empresa.",
        examples=["Desenvolvedor Backend"],
    )

    department: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Departamento ou área da empresa (opcional).",
        examples=["Tecnologia"],
    )

    tool_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Nome da ferramenta SaaS ou de IA sendo avaliada.",
        examples=["GitHub Copilot"],
    )

    tool_type: ToolTypeEnum = Field(
        ...,
        description="Tipo da ferramenta: 'IA' ou 'SAAS'.",
        examples=["IA"],
    )

    business_context: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Contexto de negócio que justifica o uso da ferramenta (opcional).",
        examples=["Uso para produtividade em desenvolvimento de software."],
    )

    # Exemplo exibido no Swagger
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "person_name": "João Silva",
                "role": "Desenvolvedor Backend",
                "department": "Tecnologia",
                "tool_name": "GitHub Copilot",
                "tool_type": "IA",
                "business_context": "Uso para produtividade em desenvolvimento de software.",
            }
        },
    )


# -------------------------------------------------------
# Schema de Resposta (Response DTO)
# -------------------------------------------------------

class EvaluationResponse(BaseModel):
    """
    Resposta da avaliação retornada pela API.

    Contém a decisão, score, nível de risco, justificativa
    e demais informações produzidas pela IA.
    """

    decision: DecisionEnum = Field(
        ...,
        description="Decisão final: RECOMENDADO, NAO_RECOMENDADO ou ANALISE_HUMANA.",
    )

    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Pontuação de 0 a 100 representando a adequação do acesso.",
    )

    risk_level: RiskLevelEnum = Field(
        ...,
        description="Nível de risco: BAIXO, MEDIO ou ALTO.",
    )

    justification: str = Field(
        ...,
        description="Justificativa detalhada da decisão tomada pela IA.",
    )

    recommended_access: str = Field(
        ...,
        description="Tipo de acesso recomendado (ex: acesso padrão, restrito, etc.).",
    )

    main_use_cases: list[str] = Field(
        default_factory=list,
        description="Lista dos principais casos de uso da ferramenta para o cargo.",
    )

    conditions: list[str] = Field(
        default_factory=list,
        description="Lista de condições ou restrições para o uso da ferramenta.",
    )

    provider: str = Field(
        ...,
        description="Provider de IA utilizado para gerar a avaliação (ex: openai, gemini).",
    )

    model: str = Field(
        ...,
        description="Modelo de IA utilizado (ex: gpt-4o, gemini-pro).",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "decision": "RECOMENDADO",
                "score": 85,
                "risk_level": "MEDIO",
                "justification": "A ferramenta possui forte aderência ao cargo e pode aumentar produtividade.",
                "recommended_access": "Acesso padrão com política de uso.",
                "main_use_cases": [
                    "Apoio em desenvolvimento",
                    "Geração de testes",
                    "Documentação técnica",
                ],
                "conditions": ["Não inserir credenciais ou dados sensíveis."],
                "provider": "openai",
                "model": "gpt-4o",
            }
        },
    )
