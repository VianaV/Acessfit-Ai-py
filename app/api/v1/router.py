"""
app/api/v1/router.py
----------------------
Roteador principal da versão 1 da API.

Responsabilidade:
- Agrupar todos os controllers da v1 sob o prefixo /api/v1.
- Permitir que o main.py inclua apenas este router,
  mantendo o arquivo principal limpo e organizado.

Para adicionar novos controllers:
1. Crie o arquivo em app/api/v1/
2. Importe o router do controller aqui.
3. Inclua com router.include_router().
"""

from fastapi import APIRouter

from app.api.v1 import evaluation_controller

# -------------------------------------------------------
# Router principal da v1
# -------------------------------------------------------
# O prefixo /api/v1 é aplicado a todas as rotas incluídas aqui.
api_v1_router = APIRouter(prefix="/api/v1")

# -------------------------------------------------------
# Inclusão dos controllers
# -------------------------------------------------------
# Cada controller tem seu próprio router, incluído aqui.
# Isso permite que cada controller defina seus próprios
# prefixos, tags e configurações sem impactar os outros.
api_v1_router.include_router(evaluation_controller.router)
