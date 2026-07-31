"""
app/core/config.py
------------------
Centraliza todas as configurações da aplicação usando pydantic-settings.

O pydantic-settings lê variáveis de ambiente automaticamente (e do arquivo .env),
validando os tipos e fornecendo valores padrão quando aplicável.

Isso garante que a aplicação nunca suba com configurações faltando ou inválidas.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Classe principal de configurações da aplicação.

    Cada atributo representa uma variável de ambiente.
    O pydantic-settings cuida da leitura, validação e conversão de tipos.
    """

    # -------------------------------------------------------
    # Ambiente da aplicação
    # -------------------------------------------------------
    # Valores típicos: "development", "staging", "production"
    APP_ENV: str = "development"

    # -------------------------------------------------------
    # Configurações da OpenAI
    # -------------------------------------------------------
    # Chave de API da OpenAI — NUNCA commitar com valor real
    OPENAI_API_KEY: str

    # Modelo a ser utilizado nas chamadas de IA
    # Pode ser sobrescrito pelo .env sem mudar o código
    OPENAI_MODEL: str = "gpt-4o"

    # -------------------------------------------------------
    # Configurações do servidor / aplicação
    # -------------------------------------------------------
    APP_NAME: str = "access-fit-ai"
    APP_VERSION: str = "1.0.0"

    # -------------------------------------------------------
    # Configuração do pydantic-settings
    # -------------------------------------------------------
    # model_config define como a classe se comporta:
    # - env_file: lê variáveis do arquivo .env na raiz
    # - env_file_encoding: encoding do arquivo .env
    # - case_sensitive: variáveis de ambiente diferenciam maiúsculas/minúsculas
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# -------------------------------------------------------
# Instância global de configurações
# -------------------------------------------------------
# Importada pelos outros módulos como: from app.core.config import settings
# O objeto é criado uma única vez (singleton implícito por módulo em Python).
settings = Settings()
