"""
app/integrations/openai_client.py
-----------------------------------
Encapsula toda comunicação com a API da OpenAI.

Responsabilidades desta camada:
- Inicializar o cliente OpenAI com a chave de API.
- Enviar mensagens e receber respostas.
- Tratar erros específicos da API (rate limit, timeout, etc.).
- Retornar o texto bruto da resposta para o serviço processar.

O que NÃO deve existir aqui:
- Lógica de negócio.
- Construção de prompts (isso fica em prompts.py).
- Validação de schemas (isso fica no serviço).
"""

import json
import logging
from openai import OpenAI, OpenAIError, RateLimitError, APITimeoutError

from app.core.config import settings
from app.infra.logging_config import get_logger

logger = get_logger(__name__)


class OpenAIClient:
    """
    Cliente de integração com a OpenAI.

    Encapsula a lógica de chamada à API, incluindo:
    - Configuração do cliente com a chave de API.
    - Chamada ao endpoint de chat completions.
    - Tratamento de erros da API.
    - Extração e retorno da resposta em formato de texto.

    Preparado para ser substituído ou complementado por outros
    providers (ex: Gemini) sem impacto no restante da aplicação.
    """

    # Nome do provider — usado no campo "provider" da response
    PROVIDER_NAME = "openai"

    def __init__(self):
        """
        Inicializa o cliente OpenAI usando a chave da variável de ambiente.
        A chave é lida das configurações centralizadas (settings).
        """
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        logger.info(f"OpenAIClient inicializado | model={self.model}")

    def evaluate(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Envia os prompts para a OpenAI e retorna o JSON da resposta.

        Usa o modo de chat completion com duas mensagens:
        - system: define o comportamento e as regras do modelo.
        - user: fornece os dados específicos da avaliação.

        Args:
            system_prompt: Instrução de comportamento para o modelo.
            user_prompt: Dados da avaliação a ser processada.

        Returns:
            Dicionário Python com os campos retornados pela IA.

        Raises:
            RateLimitError: Quando a cota da API é atingida.
            APITimeoutError: Quando a requisição expira.
            OpenAIError: Para outros erros da API OpenAI.
            ValueError: Quando a resposta não é um JSON válido.
        """
        logger.debug("Enviando requisição para OpenAI...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                # Temperatura 0 = respostas mais determinísticas e consistentes
                temperature=0.2,
                # Limita o tamanho da resposta para evitar custos excessivos
                max_tokens=1500,
                # response_format JSON mode — força saída em JSON válido
                # (disponível em modelos compatíveis como gpt-4o e gpt-4-turbo)
                response_format={"type": "json_object"},
            )

            # Extrai o conteúdo textual da primeira escolha
            raw_content = response.choices[0].message.content
            logger.debug(f"Resposta bruta da OpenAI: {raw_content}")

            # Converte o JSON recebido para dicionário Python
            parsed = json.loads(raw_content)

            # Adiciona metadados do provider e modelo ao resultado
            parsed["provider"] = self.PROVIDER_NAME
            parsed["model"] = self.model

            logger.info(f"Avaliação concluída | decision={parsed.get('decision')} | score={parsed.get('score')}")
            return parsed

        except RateLimitError as e:
            logger.error(f"Rate limit atingido na OpenAI: {e}")
            raise RuntimeError("Limite de requisições da OpenAI atingido. Tente novamente em instantes.") from e

        except APITimeoutError as e:
            logger.error(f"Timeout na chamada à OpenAI: {e}")
            raise RuntimeError("A requisição para a OpenAI excedeu o tempo limite.") from e

        except json.JSONDecodeError as e:
            logger.error(f"Resposta da OpenAI não é JSON válido: {e}")
            raise ValueError("A IA retornou uma resposta em formato inválido.") from e

        except OpenAIError as e:
            logger.error(f"Erro na API da OpenAI: {e}")
            raise RuntimeError(f"Erro ao chamar a OpenAI: {str(e)}") from e
