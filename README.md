# Access Fit AI — Backend

> API para avaliação inteligente de acesso a ferramentas SaaS e de IA nas empresas.

---

## 🎯 Objetivo

O **Access Fit AI** avalia se uma pessoa, com determinado cargo e departamento, deve ou não ter acesso a uma ferramenta SaaS ou de IA. A análise considera:

- **Aderência ao cargo**: o cargo está alinhado ao propósito da ferramenta?
- **Ganho de produtividade**: a ferramenta traz valor real para essa função?
- **Risco de segurança**: existe risco de uso indevido ou vazamento de dados?
- **Exposição de dados**: a ferramenta pode expor dados sensíveis, PII ou propriedade intelectual?
- **Necessidade real**: a ferramenta é necessária para a função ou é apenas conveniência?

---

## 🚀 Como instalar e rodar

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/access-fit-backend.git
cd access-fit-backend
```

### 2. Crie e ative o ambiente virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o .env com sua chave da OpenAI
```

Conteúdo do `.env`:

```env
APP_ENV=development
OPENAI_API_KEY=sk-...sua-chave-aqui...
OPENAI_MODEL=gpt-4o
```

> 🔑 Obtenha sua chave em: https://platform.openai.com/api-keys

### 5. Rode a aplicação

```bash
uvicorn app.main:app --reload
```

A API estará disponível em: **http://localhost:8000**

---

## 📖 Documentação interativa

| Interface | URL |
|-----------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI JSON | http://localhost:8000/openapi.json |

---

## 🔌 Endpoints

### `GET /health` — Health Check

Verifica se a API está no ar.

**Response:**
```json
{
  "status": "ok",
  "service": "access-fit-ai",
  "version": "1.0.0",
  "environment": "development"
}
```

---

### `POST /api/v1/evaluations` — Avaliação individual

Avalia se uma pessoa deve ter acesso a uma ferramenta.

**Request:**
```json
{
  "person_name": "João Silva",
  "role": "Desenvolvedor Backend",
  "department": "Tecnologia",
  "tool_name": "GitHub Copilot",
  "tool_type": "IA",
  "business_context": "Uso para produtividade em desenvolvimento de software."
}
```

**Campos:**
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `person_name` | string | Não | Nome da pessoa |
| `role` | string | **Sim** | Cargo ou função |
| `department` | string | Não | Departamento |
| `tool_name` | string | **Sim** | Nome da ferramenta |
| `tool_type` | `"IA"` ou `"SAAS"` | **Sim** | Tipo da ferramenta |
| `business_context` | string | Não | Contexto de negócio |

**Response:**
```json
{
  "decision": "RECOMENDADO",
  "score": 85,
  "risk_level": "MEDIO",
  "justification": "A ferramenta possui forte aderência ao cargo e pode aumentar produtividade.",
  "recommended_access": "Acesso padrão com política de uso.",
  "main_use_cases": [
    "Apoio em desenvolvimento",
    "Geração de testes",
    "Documentação técnica"
  ],
  "conditions": [
    "Não inserir credenciais ou dados sensíveis."
  ],
  "provider": "openai",
  "model": "gpt-4o"
}
```

**Valores possíveis:**
- `decision`: `RECOMENDADO` | `NAO_RECOMENDADO` | `ANALISE_HUMANA`
- `risk_level`: `BAIXO` | `MEDIO` | `ALTO`

---

### `POST /api/v1/evaluations/batch` — Avaliação em lote

Avalia múltiplos acessos em uma única requisição (máximo 50).

**Request:**
```json
[
  {
    "person_name": "João Silva",
    "role": "Desenvolvedor Backend",
    "department": "Tecnologia",
    "tool_name": "GitHub Copilot",
    "tool_type": "IA",
    "business_context": "Uso para produtividade em desenvolvimento de software."
  },
  {
    "person_name": "Maria Souza",
    "role": "Auxiliar Administrativo",
    "department": "Administrativo",
    "tool_name": "Figma",
    "tool_type": "SAAS",
    "business_context": "Ferramenta de design e prototipação."
  }
]
```

**Response:** Lista de respostas no mesmo formato da avaliação individual.

---

## 🏗️ Arquitetura

```
access-fit-backend/
├── app/
│   ├── main.py                          # Ponto de entrada da aplicação FastAPI
│   ├── api/
│   │   └── v1/
│   │       ├── router.py                # Agrega os routers da v1
│   │       └── evaluation_controller.py # Endpoints de avaliação
│   ├── core/
│   │   └── config.py                    # Configurações via pydantic-settings
│   ├── schemas/
│   │   └── evaluation_schema.py         # DTOs de request e response (Pydantic)
│   ├── services/
│   │   ├── evaluation_service.py        # Lógica de negócio principal
│   │   └── rule_engine.py              # Regras heurísticas pré-IA
│   ├── integrations/
│   │   ├── openai_client.py             # Cliente de integração com a OpenAI
│   │   └── prompts.py                   # Prompts de sistema e usuário
│   └── infra/
│       └── logging_config.py            # Configuração centralizada de logging
├── .env.example                         # Exemplo de variáveis de ambiente
├── requirements.txt                     # Dependências Python
└── README.md                            # Esta documentação
```

### Responsabilidade de cada camada

| Camada | Arquivo | Responsabilidade |
|--------|---------|-----------------|
| **Controller** | `evaluation_controller.py` | Receber HTTP request, retornar HTTP response |
| **Service** | `evaluation_service.py` | Orquestrar a lógica de negócio |
| **Rule Engine** | `rule_engine.py` | Regras heurísticas pré-IA |
| **Integration** | `openai_client.py` | Chamada à API da OpenAI |
| **Prompts** | `prompts.py` | Templates de prompt para a IA |
| **Schema** | `evaluation_schema.py` | Contratos de dados (DTOs) |
| **Config** | `config.py` | Configurações e variáveis de ambiente |
| **Infra** | `logging_config.py` | Infraestrutura de observabilidade |

### Fluxo de uma requisição

```
Cliente HTTP
    ↓
FastAPI (main.py)
    ↓ valida request com Pydantic
Controller (evaluation_controller.py)
    ↓ delega ao serviço
EvaluationService (evaluation_service.py)
    ↓ análise heurística
RuleEngine (rule_engine.py) → gera contexto adicional
    ↓ monta prompt
Prompts (prompts.py)
    ↓ chama a IA
OpenAIClient (openai_client.py) → OpenAI API
    ↓ valida resposta
EvaluationResponse (Pydantic)
    ↓ retorna
Controller → FastAPI → Cliente HTTP
```

---

## 🔄 Próximos passos

### Integrações
- [ ] **Gemini / Claude / outros providers**: Criar `GeminiClient` em `app/integrations/gemini_client.py` e alternar via config.
- [ ] **Planilha Excel**: Exportar avaliações em lote para `.xlsx` usando `openpyxl` ou `pandas`.
- [ ] **Slack / Teams**: Notificar gestores quando uma avaliação precisar de análise humana.

### Persistência
- [ ] **Banco de dados**: Adicionar SQLAlchemy ou SQLModel com PostgreSQL/SQLite para salvar histórico de avaliações.

---

## 🧪 Testes e cobertura

Instale as dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

Execute a suíte completa:

```bash
pytest
```

Os testes unitários validam schemas, prompts, regras, serviço, logging e o
cliente OpenAI. Os testes de integração exercitam os endpoints FastAPI sem
realizar chamadas externas: a resposta da OpenAI é simulada para manter a suíte
rápida, determinística e sem custo.

O projeto exige 100% de cobertura de linhas e ramificações da pasta `app`. O
relatório detalhado também é criado em `htmlcov/index.html`.

Para uma referência técnica curta nas próximas manutenções, consulte
`PROJECT_CONTEXT.md`.
- [ ] **Cache Redis**: Cachear avaliações idênticas para reduzir custo de API.

### Segurança e governança
- [ ] **Autenticação JWT**: Proteger os endpoints com tokens de acesso.
- [ ] **Rate limiting**: Limitar chamadas por usuário/empresa.
- [ ] **Audit log**: Registrar todas as avaliações com timestamp, usuário e decisão.

### Operacional
- [ ] **Docker**: Containerizar a aplicação para deploy em qualquer ambiente.
- [ ] **CI/CD**: Adicionar pipeline de testes e deploy automático.
- [ ] **Testes**: Implementar testes unitários para RuleEngine e EvaluationService.

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Versão | Função |
|------------|--------|--------|
| Python | 3.11+ | Linguagem principal |
| FastAPI | 0.115 | Framework web |
| Uvicorn | 0.32 | Servidor ASGI |
| Pydantic v2 | 2.10 | Validação de dados |
| pydantic-settings | 2.6 | Configurações via env |
| OpenAI SDK | 1.58 | Integração com GPT |
| python-dotenv | 1.0 | Leitura do .env |

---

## 📄 Licença

MIT License — use, modifique e distribua livremente.
