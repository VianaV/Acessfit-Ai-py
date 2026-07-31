"""
app/services/evaluation_service.py
-------------------------------------
Serviço principal de avaliação de acessos.

Esta camada é o coração da aplicação. Responsabilidades:
1. Receber o request já validado pelo controller.
2. Chamar a RuleEngine para análise preliminar.
3. Montar o prompt completo com os dados + contexto das regras.
4. Chamar o cliente de IA (OpenAIClient).
5. Validar a resposta da IA usando o schema Pydantic.
6. Retornar o resultado estruturado ao controller.

O que NÃO deve existir aqui:
- Código de roteamento HTTP (isso fica no controller).
- Chamadas diretas à API da OpenAI (isso fica no openai_client).
- Prompts hard-coded (isso fica em prompts.py).
"""

import asyncio
from typing import List

from app.schemas.evaluation_schema import EvaluationRequest, EvaluationResponse
from app.services.rule_engine import RuleEngine
from app.integrations.openai_client import OpenAIClient
from app.integrations.prompts import SYSTEM_PROMPT, build_evaluation_prompt
from app.infra.logging_config import get_logger

logger = get_logger(__name__)


class EvaluationService:
    """
    Orquestra o fluxo completo de avaliação de acesso a ferramentas.

    Usa injeção de dependências simples para facilitar testes unitários:
    - RuleEngine pode ser substituída por uma versão mock.
    - OpenAIClient pode ser substituído por outro provider de IA.
    """

    def __init__(self):
        """
        Inicializa o serviço com as dependências necessárias.
        RuleEngine é stateless (sem estado), então pode ser compartilhada.
        OpenAIClient inicializa a conexão com a API.
        """
        self.rule_engine = RuleEngine()
        self.ai_client = OpenAIClient()
        logger.info("EvaluationService inicializado.")

    def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        """
        Executa uma avaliação individual de acesso.

        Fluxo:
        1. RuleEngine analisa o request → gera contexto adicional.
        2. Prompt é montado com dados + contexto.
        3. OpenAIClient envia o prompt e recebe a resposta JSON.
        4. Resposta é validada e retornada como EvaluationResponse.

        Args:
            request: Dados validados da requisição.

        Returns:
            EvaluationResponse com decisão, score, risco e detalhes.

        Raises:
            RuntimeError: Se a chamada à IA falhar.
            ValueError: Se a resposta da IA não puder ser validada.
        """
        person_label = request.person_name or request.role
        logger.info(
            f"Iniciando avaliação | pessoa='{person_label}' | "
            f"ferramenta='{request.tool_name}' | tipo='{request.tool_type}'"
        )

        # Passo 1: Análise preliminar com a RuleEngine
        rule_context = self.rule_engine.analyze(request)
        logger.debug(f"Contexto da RuleEngine:\n{rule_context}")

        # Passo 2: Construção do prompt de usuário
        user_prompt = build_evaluation_prompt(request, rule_context)

        # Passo 3: Chamada à IA
        raw_result = self.ai_client.evaluate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # Passo 4: Validação da resposta usando Pydantic
        # Se a IA retornar dados com tipos errados ou campos faltando,
        # o Pydantic lança ValidationError com mensagem clara.
        try:
            response = EvaluationResponse(**raw_result)
        except Exception as e:
            logger.error(f"Erro ao validar resposta da IA: {e} | raw={raw_result}")
            raise ValueError(f"Resposta da IA inválida: {str(e)}") from e

        logger.info(
            f"Avaliação concluída | decision={response.decision} | "
            f"score={response.score} | risk={response.risk_level}"
        )
        return response

    def evaluate_batch(self, requests: List[EvaluationRequest]) -> List[EvaluationResponse]:
        """
        Executa avaliações em lote, processando cada item sequencialmente.

        Nota: Por questão de custo e rate limit da API, as chamadas são feitas
        sequencialmente por padrão. Para volume alto, considere implementar
        throttling ou processamento assíncrono com asyncio.gather.

        Args:
            requests: Lista de requests para avaliação.

        Returns:
            Lista de EvaluationResponse, um por request.
            Em caso de erro em um item, retorna uma resposta de fallback
            para não interromper o processamento dos demais.
        """
        logger.info(f"Iniciando avaliação em lote | total={len(requests)} itens")
        results = []

        for index, request in enumerate(requests, start=1):
            logger.info(f"Processando item {index}/{len(requests)}")
            try:
                result = self.evaluate(request)
                results.append(result)
            except Exception as e:
                # Em caso de erro, cria uma resposta de fallback para não travar o lote
                logger.error(f"Erro ao processar item {index}: {e}")
                fallback = self._build_error_response(request, str(e))
                results.append(fallback)

        logger.info(f"Lote concluído | {len(results)} avaliações processadas")
        return results

    def _build_error_response(self, request: EvaluationRequest, error_msg: str) -> EvaluationResponse:
        """
        Cria uma resposta de fallback quando ocorre erro em um item do lote.

        Em vez de lançar exceção e abortar o lote inteiro, retorna uma resposta
        sinalizada como ANALISE_HUMANA com a mensagem de erro na justificativa.

        Args:
            request: O request que causou o erro.
            error_msg: Mensagem de erro para inclusão na justificativa.

        Returns:
            EvaluationResponse com decisão ANALISE_HUMANA e detalhes do erro.
        """
        from app.schemas.evaluation_schema import DecisionEnum, RiskLevelEnum
        from app.core.config import settings

        return EvaluationResponse(
            decision=DecisionEnum.ANALISE_HUMANA,
            score=0,
            risk_level=RiskLevelEnum.ALTO,
            justification=f"Erro ao processar avaliação automaticamente: {error_msg}. Requer análise manual.",
            recommended_access="Suspender acesso até análise humana.",
            main_use_cases=[],
            conditions=["Aguardar análise humana antes de conceder acesso."],
            provider="system",
            model="fallback",
        )
