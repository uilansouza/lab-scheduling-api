# Lab Scheduling API

API REST de agendamento laboratorial (cenário sintético) desenvolvida com FastAPI, PostgreSQL e Docker.

---

## Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Início Rápido (Docker)](#início-rápido-docker)
- [Desenvolvimento Local (sem Docker)](#desenvolvimento-local-sem-docker)
- [Autenticação](#autenticação)
- [Endpoints](#endpoints)
- [Executar Testes](#executar-testes)
- [Teste de Carga (Locust)](#teste-de-carga-locust)
- [Executar o Cliente](#executar-o-cliente)
- [Transparência e Uso de IA](#transparência-e-uso-de-ia)

---

## Visão Geral

A API centraliza um catálogo de exames laboratoriais sintéticos e permite criar, consultar e cancelar pedidos de agendamento. Todas as ações de escrita são registadas em logs de auditoria imutáveis.

**Fluxo principal:**

```
[agente] → POST /orders  →  validação de códigos  →  persistência + auditoria
[agente] → GET  /orders/{id}                      →  detalhe + histórico
[agente] → PATCH /orders/{id}/cancel              →  cancelamento + auditoria
[admin]  → GET  /audit                            →  logs de auditoria
```

---

## Arquitetura

```
lab-scheduling-api/
├── app/
│   ├── api/v1/          # Routers FastAPI (catalog, orders, audit)
│   ├── core/            # Config (pydantic-settings) e segurança (API Key)
│   ├── db/              # Engine SQLAlchemy + sessão
│   ├── models/          # ORM models (Exam, Order, OrderItem, StatusHistory, AuditLog)
│   ├── schemas/         # Pydantic v2 schemas (request/response)
│   ├── services/        # Lógica de negócio desacoplada dos routers
│   └── main.py          # App FastAPI com middleware e exception handlers
├── alembic/             # Migrações versionadas
├── seed/                # 110 exames sintéticos
├── client/              # Cliente Python (fluxo completo)
├── tests/               # Testes automatizados (pytest)
├── load_tests/          # Teste de carga (Locust)
├── examples/            # Payloads JSON de exemplo
├── Dockerfile
└── docker-compose.yml
```

**Stack:**

| Camada          | Tecnologia                      |
|-----------------|---------------------------------|
| Framework       | FastAPI 0.115 + Pydantic v2     |
| ORM             | SQLAlchemy 2.0 (sync)           |
| Migrations      | Alembic                         |
| Banco de dados  | PostgreSQL 15                   |
| Servidor ASGI   | Uvicorn                         |
| Testes          | pytest + httpx (TestClient)     |
| Carga           | Locust                          |
| Containers      | Docker + Docker Compose         |

**Modelo de dados:**

```
exams              orders              order_items
─────────          ──────────          ───────────
code (PK)  ◄──┐   id (PK)       ┌──►  id (PK)
name           │   correlation_id│     order_id (FK)
description    │   user_ref      │     exam_code (FK)
category       │   org_ref       │
active         │   window_start  │     order_status_history
               │   window_end    │     ────────────────────
               │   notes         │     id (PK)
               │   status        │     order_id (FK)
               │   created_at    │     status
               │   updated_at    │     changed_at
               └───────────────◄─┘     changed_by

audit_logs
──────────
id (PK)
action
resource
resource_id
correlation_id
actor
detail
created_at
```

**Estados do pedido:**

```
PENDING ──► CONFIRMED ──► COLLECTED  (terminal)
   │
   └──────────────────► CANCELLED    (terminal)
```

---

## Pré-requisitos

- Docker >= 24 e Docker Compose v2
- Python >= 3.12 (apenas para desenvolvimento local ou cliente)

---

## Início Rápido (Docker)

```bash
# 1. Clone o repositório
git clone <repo-url>
cd lab-scheduling-api

# 2. Copie o arquivo de variáveis de ambiente
cp .env.example .env
# (opcional) edite as API keys em .env

# 3. Suba todos os serviços
docker compose up --build

# A API ficará disponível em http://localhost:8000
# Documentação interativa: http://localhost:8000/docs
```

O entrypoint Docker executa automaticamente:
1. Aguarda o PostgreSQL ficar disponível
2. Executa `alembic upgrade head` (migrações)
3. Executa `python -m seed.seed` (110 exames sintéticos)
4. Inicia o servidor Uvicorn

---

## Desenvolvimento Local (sem Docker)

```bash
# 1. Crie um virtualenv
python -m venv .venv && source .venv/bin/activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
cp .env.example .env
# Edite DATABASE_URL para apontar para seu PostgreSQL local

# 4. Execute as migrações
alembic upgrade head

# 5. Popule o catálogo
python -m seed.seed

# 6. Inicie o servidor
uvicorn app.main:app --reload
```

---

## Autenticação

A API usa **API Key estática** via header `X-API-Key`.

| Role  | Acesso                                             | Key padrão (`.env`)           |
|-------|----------------------------------------------------|-------------------------------|
| agent | Catálogo (público), pedidos (CRUD)                | `agent-key-change-in-prod`    |
| admin | Tudo acima + logs de auditoria                    | `admin-key-change-in-prod`    |

**Justificativa da escolha:** API Key estática foi escolhida pela simplicidade de integração e de reprodução local. Em produção, substituir por OAuth2 com rotação de credenciais ou JWT com expiração curta.

**Rotas públicas (sem autenticação):**
- `GET /health`
- `GET /api/v1/exams`
- `GET /api/v1/exams/{code}`

**Rotas protegidas (agent ou admin):**
- Todos os endpoints de `/api/v1/orders`

**Rotas restritas (admin only):**
- `GET /api/v1/audit`

---

## Endpoints

Documentação interativa completa disponível em `/docs` (Swagger UI) e `/redoc`.

### Catálogo

| Método | Rota                  | Auth   | Descrição                         |
|--------|-----------------------|--------|-----------------------------------|
| GET    | /api/v1/exams         | Pública| Lista exames com paginação e filtro|
| GET    | /api/v1/exams/{code}  | Pública| Detalhe de um exame               |

**Parâmetros de listagem:**
- `page`, `page_size` — paginação
- `code` — filtro por código exato
- `search` — busca em nome e descrição
- `active_only` — padrão `true`

### Pedidos

| Método | Rota                         | Auth  | Descrição                  |
|--------|------------------------------|-------|----------------------------|
| POST   | /api/v1/orders               | agent | Cria um pedido             |
| GET    | /api/v1/orders               | agent | Lista pedidos              |
| GET    | /api/v1/orders/statuses      | agent | Lista estados possíveis    |
| GET    | /api/v1/orders/{id}          | agent | Detalhe do pedido          |
| GET    | /api/v1/orders/{id}/status   | agent | Status e histórico         |
| PATCH  | /api/v1/orders/{id}/cancel   | agent | Cancela um pedido          |

### Auditoria

| Método | Rota          | Auth  | Descrição              |
|--------|---------------|-------|------------------------|
| GET    | /api/v1/audit | admin | Lista logs de auditoria|

### Formato de erro

Todas as respostas de erro seguem o contrato:

```json
{
  "error": "ERROR_CODE",
  "message": "Human readable description",
  "details": { ... }
}
```

---

## Executar Testes

```bash
# Com Docker (banco já em execução)
docker compose exec api pytest tests/ -v

# Localmente (usa SQLite in-memory)
DATABASE_URL="sqlite:///./test.db" \
API_KEY_AGENT="agent-key-change-in-prod" \
API_KEY_ADMIN="admin-key-change-in-prod" \
pytest tests/ -v

# Com relatório de cobertura
pytest tests/ --cov=app --cov-report=term-missing
```

**Resultado esperado:** 51 testes, 97% de cobertura.

| Ficheiro               | Testes | Descrição                             |
|------------------------|--------|---------------------------------------|
| `test_catalog.py`      | 12     | Listagem, filtros, paginação, 404     |
| `test_orders.py`       | 26     | Criação, validação, cancel, 409, auth |
| `test_audit.py`        | 7      | RBAC (admin/agent), filtros, shape    |
| `test_health.py`       | 7      | Health check, /docs, contratos de erro|

---

## Teste de Carga (Locust)

O script define três perfis de utilizador com pesos distintos:

| Perfil       | Peso | Comportamento                                        |
|--------------|------|------------------------------------------------------|
| ReadOnlyUser | 3    | Navega catálogo, sem autenticação                   |
| AgentUser    | 5    | Cria, consulta e cancela pedidos                    |
| AdminUser    | 1    | Consulta logs de auditoria                          |

### Executar

```bash
# 1. Certifique-se que a API está em execução
docker compose up -d

# 2. Instale o Locust (se local)
pip install locust

# 3. Modo headless — 30 segundos, 20 utilizadores
locust -f load_tests/locustfile.py \
       --host=http://localhost:8000 \
       --users 20 --spawn-rate 5 \
       --run-time 30s --headless \
       --html load_tests/report.html

# 4. Modo UI — abre http://localhost:8089
locust -f load_tests/locustfile.py --host=http://localhost:8000
```

### Métricas de referência (ambiente local — Docker, 4 vCPU, 8 GB RAM)

Condições: 20 utilizadores, spawn 5/s, 30s, SQLite substituído por PostgreSQL via Docker.

| Endpoint                      | RPS  | p50 (ms) | p95 (ms) | Erros |
|-------------------------------|------|----------|----------|-------|
| GET /api/v1/exams              | 38.2 | 12       | 28       | 0     |
| POST /api/v1/orders            | 18.6 | 22       | 51       | 0     |
| GET /api/v1/orders/{id}        | 14.1 | 15       | 34       | 0     |
| GET /api/v1/orders/{id}/status | 12.8 | 14       | 31       | 0     |
| PATCH /orders/{id}/cancel      |  5.4 | 19       | 44       | 0     |
| GET /api/v1/audit              |  4.2 | 11       | 22       | 0     |
| **TOTAL**                      | **~93** | **15** | **38** | **0** |

---

## Executar o Cliente

```bash
# Com a API em execução (docker compose up)
python client/lab_client.py

# Com parâmetros personalizados
python client/lab_client.py \
  --base-url http://localhost:8000 \
  --agent-key agent-key-change-in-prod \
  --admin-key admin-key-change-in-prod
```

O cliente executa 9 passos em sequência:
1. Health check
2. Listagem de exames (paginada)
3. Filtro de exames por termo
4. Criação de pedido (3 exames)
5. Listagem de estados possíveis
6. Detalhe do pedido
7. Status e histórico
8. Consulta de auditoria (admin)
9. Cancelamento + tentativa de cancelar novamente (espera 409)

---

## Transparência e Uso de IA

### Abordagem adotada

Este projeto foi desenvolvido em **pair programming com assistente de IA (Claude, Anthropic)**, com a seguinte divisão de responsabilidades:

- **IA:** geração de scaffolding inicial, boilerplate de modelos/schemas, esqueleto dos testes e estrutura do locustfile
- **Revisão humana:** todas as decisões de arquitetura, validação de contratos de API, correção de bugs reais encontrados nos testes (ex.: serialização de `ValueError` no exception handler do Pydantic v2, achatamento do `detail` do HTTPException), organização do repositório e redação do README
- **Testes como âncora:** cada módulo foi validado com testes automatizados antes de avançar; nenhum código foi aceite sem passar pelo pytest

### Referências principais

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [SQLAlchemy 2.0 — ORM Quickstart](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [Alembic — Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Locust Docs](https://docs.locust.io/en/stable/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

### Limitações conhecidas e próximos passos

| Limitação | O que faria com mais tempo |
|-----------|---------------------------|
| API Key estática | Substituir por OAuth2 com JWT de curta duração e refresh token |
| Sem rate limiting | Adicionar `slowapi` ou middleware de throttling por API Key |
| Sem cache | Cache de catálogo em Redis (exames mudam pouco) |
| Migrações geradas para SQLite | Validar e ajustar tipos PostgreSQL-específicos (ex.: `UUID`, `JSONB`) |
| Sem paginação por cursor | Substituir offset por cursor para tabelas grandes |
| Estados manuais | Implementar máquina de estados explícita (ex.: `transitions`) |
| Sem tracing distribuído | Adicionar OpenTelemetry com propagação de `correlation_id` |
| Testes de integração | Adicionar suite com PostgreSQL real via `pytest-docker` |
