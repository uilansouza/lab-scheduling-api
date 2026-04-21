import logging
import time
import uuid

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import catalog, orders, audit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("lab_api")

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="""
## Lab Scheduling API

API de agendamento laboratorial sintético.

### Autenticação
Todas as rotas protegidas exigem o header `X-API-Key`.

| Papel  | Acesso                                      |
|--------|---------------------------------------------|
| agent  | Catálogo (público), pedidos (CRUD)          |
| admin  | Tudo acima + logs de auditoria              |

### Códigos de erro
Todas as respostas de erro seguem o formato:
```json
{"error": "ERROR_CODE", "message": "Human readable message", "details": {...}}
```
""",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Catalog", "description": "Exam catalog — public access"},
        {"name": "Orders", "description": "Order management — requires agent or admin key"},
        {"name": "Audit", "description": "Audit logs — requires admin key"},
        {"name": "Health", "description": "Service health"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handlers ────────────────────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Flatten detail dict to top-level so clients get {error, message} directly."""
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {"error": "HTTP_ERROR", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Pydantic v2 puts a ValueError in ctx — strip it so json.dumps doesn't choke
    def _sanitize(errors):
        clean = []
        for e in errors:
            entry = {k: v for k, v in e.items() if k != "ctx"}
            ctx = e.get("ctx", {})
            if ctx:
                entry["ctx"] = {k: str(v) for k, v in ctx.items()}
            clean.append(entry)
        return clean

    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": _sanitize(exc.errors()),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
    )


# ── Request logging middleware ────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "[%s] %s %s → %d (%.1fms)",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.1f}"
    return response


# ── Routers ───────────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(catalog.router, prefix=API_PREFIX)
app.include_router(orders.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"], summary="Health check")
def health():
    return {"status": "ok", "version": settings.APP_VERSION}
