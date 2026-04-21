from enum import Enum
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class Role(str, Enum):
    AGENT = "agent"
    ADMIN = "admin"


def _resolve_role(api_key: str | None) -> Role:
    if api_key == settings.API_KEY_ADMIN:
        return Role.ADMIN
    if api_key == settings.API_KEY_AGENT:
        return Role.AGENT
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "UNAUTHORIZED", "message": "Invalid or missing API key"},
    )


def require_agent(api_key: str | None = Security(api_key_header)) -> Role:
    """Allows agent and admin roles."""
    return _resolve_role(api_key)


def require_admin(api_key: str | None = Security(api_key_header)) -> Role:
    """Allows admin role only."""
    role = _resolve_role(api_key)
    if role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "Admin access required"},
        )
    return role
