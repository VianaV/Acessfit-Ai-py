"""
app/api/v1/evaluation_controller.py
--------------------------------------
Controller (ou "handler") dos endpoints de avaliação.

Responsabilidades do controller:
- Receber a requisição HTTP do FastAPI (via Router).
- Repassar os dados validados ao serviço correspondente.
- Retornar a resposta HTTP com o resultado do serviço.

O que NÃO deve existir aqui:
- Lógica de negócio (isso fica em evaluation_service.py).
- Chamadas diretas à IA (isso fica em openai_client.py).
- Validação manual de dados (o Pydantic + FastAPI fazem isso automaticamente).
"""

from typing import List

from fastapi import APIRouter, HTTPException, status

from app.schemas.evaluation_schema import EvaluationRequest, EvaluationResponse
from app.services.evaluation_service import EvaluationService
from app.infra.logging_config import get_logger

logger = get_logger(__name__)

# -------------------------------------------------------
# Router do controller
# -------------------------------------------------------
# O prefixo e as tags são definidos no router.py principal.
# Aqui criamos um router local apenas para agrupar as rotas deste controller.
router = APIRouter()

# -------------------------------------------------------
# Instância do serviço
# -------------------------------------------------------
# Em uma aplicação maior, isso seria injetado via Depends() do FastAPI.
# Por simplicidade, instanciamos uma vez por processo.
evaluation_service = EvaluationService()


# -------------------------------------------------------
# Endpoint: Avaliação individual
# -------------------------------------------------------

@router.post(
    "/evaluations",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Avaliação individual de acesso",
    description=(
        "Avalia se uma pessoa com determinado cargo deve ter acesso "
        "a uma ferramenta SaaS ou de IA. Retorna decisão, score, "
        "nível de risco e recomendações detalhadas."
    ),
    tags=["Avaliações"],
)
def evaluate_single(request: EvaluationRequest) -> EvaluationResponse:
    """
    POST /api/v1/evaluations

    Recebe os dados da pessoa e da ferramenta, delega ao serviço
    de avaliação e retorna o resultado estruturado.

    Args:
        request: Dados validados automaticamente pelo FastAPI + Pydantic.

    Returns:
        EvaluationResponse com a decisão e detalhes da avaliação.

    Raises:
        HTTPException 422: Dados inválidos (validação Pydantic automática).
        HTTPException 500: Erro interno ao processar a avaliação.
    """
    logger.info(f"Requisição de avaliação recebida | ferramenta='{request.tool_name}'")

    try:
        result = evaluation_service.evaluate(request)
        return result
    except ValueError as e:
        # Erro de validação da resposta da IA
        logger.error(f"Erro de validação: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        # Erro de comunicação com a API da IA
        logger.error(f"Erro de runtime: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        # Erro inesperado — registra e retorna 500
        logger.exception(f"Erro inesperado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a avaliação.",
        )


# -------------------------------------------------------
# Endpoint: Avaliação em lote (batch)
# -------------------------------------------------------

@router.post(
    "/evaluations/batch",
    response_model=List[EvaluationResponse],
    status_code=status.HTTP_200_OK,
    summary="Avaliação em lote",
    description=(
        "Recebe uma lista de avaliações e processa cada uma delas. "
        "Em caso de erro em um item, retorna uma resposta de fallback "
        "para aquele item sem interromper o processamento dos demais."
    ),
    tags=["Avaliações"],
)
def evaluate_batch(requests: List[EvaluationRequest]) -> List[EvaluationResponse]:
    """
    POST /api/v1/evaluations/batch

    Processa múltiplas avaliações em sequência.
    Erros individuais não interrompem o lote — são sinalizados
    com decisão ANALISE_HUMANA na resposta daquele item.

    Args:
        requests: Lista de requests validados pelo FastAPI + Pydantic.

    Returns:
        Lista de EvaluationResponse, um por request de entrada.

    Raises:
        HTTPException 400: Lista vazia enviada.
        HTTPException 500: Erro interno inesperado.
    """
    if not requests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A lista de avaliações não pode estar vazia.",
        )

    if len(requests) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O lote não pode conter mais de 50 avaliações por requisição.",
        )

    logger.info(f"Requisição de lote recebida | total={len(requests)} itens")

    try:
        results = evaluation_service.evaluate_batch(requests)
        return results
    except Exception as e:
        logger.exception(f"Erro inesperado no lote: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar o lote de avaliações.",
        )
