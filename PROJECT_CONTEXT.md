# Contexto do projeto — Access Fit AI

Este arquivo serve como referência rápida para futuras manutenções e reduz a
necessidade de reler todo o projeto a cada alteração.

## Objetivo

API FastAPI que avalia se uma pessoa deve receber acesso a uma ferramenta de IA
ou SaaS. A decisão considera aderência ao cargo, produtividade, necessidade,
segurança e exposição de dados.

## Stack

- Python 3.11+
- FastAPI 0.115.5
- Pydantic 2.10.3 e pydantic-settings 2.6.1
- OpenAI SDK 1.58.1
- Pytest 8.3.4 e pytest-cov 6.0.0

## Arquitetura

| Área | Arquivo | Responsabilidade |
|---|---|---|
| Entrada da API | `app/main.py` | Cria o FastAPI, registra CORS, rotas, lifespan e health check |
| Controller | `app/api/v1/evaluation_controller.py` | Traduz HTTP para chamadas do serviço e trata erros |
| Serviço | `app/services/evaluation_service.py` | Orquestra regras, prompt, IA e validação da resposta |
| Regras | `app/services/rule_engine.py` | Produz sinais determinísticos de aderência, risco e necessidade |
| Integração | `app/integrations/openai_client.py` | Chama a OpenAI e converte a resposta JSON |
| Prompts | `app/integrations/prompts.py` | Define o prompt de sistema e monta o prompt da avaliação |
| Contratos | `app/schemas/evaluation_schema.py` | Define requests, responses e enums Pydantic |
| Configuração | `app/core/config.py` | Carrega variáveis de ambiente |

## Endpoints

- `GET /health`
- `POST /api/v1/evaluations`
- `POST /api/v1/evaluations/batch` (de 1 a 50 itens)

## Fluxo principal

1. FastAPI valida o JSON com `EvaluationRequest`.
2. `RuleEngine` gera observações preliminares.
3. `build_evaluation_prompt` combina request, regras e schema esperado.
4. `OpenAIClient` solicita uma resposta JSON ao modelo.
5. `EvaluationService` valida o resultado com `EvaluationResponse`.
6. O controller converte falhas conhecidas em respostas HTTP apropriadas.

No lote, uma falha isolada gera um fallback `ANALISE_HUMANA` e não interrompe os
demais itens.

## Estratégia de testes

Os testes nunca chamam a API real da OpenAI.

- `tests/unit`: schemas, prompts, motor de regras, serviço, cliente OpenAI e logging.
- `tests/integration`: aplicação FastAPI e endpoints por meio do `TestClient`.
- Chamadas externas são substituídas por objetos falsos ou mocks.
- O `pytest.ini` exige 100% de cobertura de linhas e ramificações da pasta `app`.

## Comandos

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

No Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest
```

O relatório navegável de cobertura é gerado em `htmlcov/index.html`.

## Variáveis de ambiente

Use `.env.example` como modelo. Nunca versione `.env` nem uma chave real.

- `APP_ENV`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `APP_NAME`
- `APP_VERSION`

Nos testes, `OPENAI_API_KEY` e demais valores são definidos em
`tests/conftest.py`.

## Cuidados ao alterar

- Preserve os valores dos enums expostos na API.
- Mantenha chamadas externas mockadas nos testes.
- Adicione testes para cada novo tratamento de erro ou ramificação.
- Execute `pytest` antes de empacotar ou publicar.
- Não inclua `.env`, `.venv`, caches, cobertura HTML ou metadados Git no ZIP de
  distribuição.
