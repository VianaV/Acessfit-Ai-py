"""
app/main.py
------------
Ponto de entrada da aplicação FastAPI.

Responsabilidades:
- Criar e configurar a instância do FastAPI.
- Registrar routers (endpoints) da API.
- Configurar eventos de startup e shutdown.
- Configurar middlewares globais (CORS, logging, etc.).
- Definir o endpoint de health check.

Como rodar:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.infra.logging_config import setup_logging
from app.api.v1.router import api_v1_router


# -------------------------------------------------------
# Configuração de logging (antes de qualquer coisa)
# -------------------------------------------------------
# Chamado aqui para garantir que o logging esteja configurado
# antes mesmo de o FastAPI ser inicializado.
setup_logging()

import logging
logger = logging.getLogger(__name__)


# -------------------------------------------------------
# Lifecycle: startup e shutdown
# -------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.

    O código antes do `yield` é executado no startup.
    O código depois do `yield` é executado no shutdown.

    Aqui é o lugar certo para:
    - Conectar ao banco de dados.
    - Inicializar caches.
    - Liberar recursos ao encerrar.
    """
    # --- Startup ---
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} iniciando...")
    logger.info(f"   Ambiente: {settings.APP_ENV}")
    logger.info(f"   Modelo IA: {settings.OPENAI_MODEL}")
    logger.info(f"   Docs disponíveis em: http://localhost:8000/docs")

    yield  # A aplicação roda aqui

    # --- Shutdown ---
    logger.info(f"🛑 {settings.APP_NAME} encerrando...")


# -------------------------------------------------------
# Criação da instância do FastAPI
# -------------------------------------------------------

app = FastAPI(
    title="Access Fit AI",
    description=(
        "API para avaliação de acesso a ferramentas SaaS e de IA. "
        "Analisa se um cargo/departamento deve ter acesso a uma ferramenta "
        "considerando aderência, produtividade, riscos de segurança e exposição de dados."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc (alternativa ao Swagger)
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# -------------------------------------------------------
# Middlewares
# -------------------------------------------------------

# CORS: permite que frontends (ou Postman/curl) de qualquer origem
# façam requisições à API. Em produção, restrinja allow_origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Em produção: ["https://seu-dominio.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------
# Routers
# -------------------------------------------------------

# Registra todas as rotas da v1 (evaluation, etc.)
app.include_router(api_v1_router)


# -------------------------------------------------------
# Endpoint: Health Check
# -------------------------------------------------------

@app.get(
    "/health",
    summary="Health Check",
    description="Verifica se a API está no ar e funcionando.",
    tags=["Sistema"],
)
def health_check() -> dict:
    """
    GET /health

    Retorna o status da aplicação.
    Usado por load balancers, ferramentas de monitoramento (k8s, etc.)
    e pipelines de CI/CD para verificar se o serviço está disponível.

    Returns:
        JSON com status "ok" e nome do serviço.
    """
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }
