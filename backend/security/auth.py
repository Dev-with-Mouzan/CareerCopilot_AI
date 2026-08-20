"""JWT and API-key authentication for CareerCopilot AI."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Header, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.models import User
from backend.core.schemas import UserProfile
from backend.db.session import get_db

logger = logging.getLogger(__name__)
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ─────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────────────────────


def create_access_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_expiration_minutes))
    payload = {"sub": str(user_id), "exp": expire, "iat": now}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict:
    """Decode and validate a JWT.  Returns the payload dict."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ── User resolution ──────────────────────────────────────────────────────────


async def _fetch_user(db: AsyncSession, user_id: UUID) -> UserProfile | None:
    result = await db.execute(select(User).where(User.id == user_id))
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return UserProfile(
        id=row.id,
        email=row.email,
        name=row.name,
        created_at=row.created_at,
        preferences=row.preferences or {},
    )


async def _resolve_user(token: str, db: AsyncSession) -> UserProfile:
    payload = verify_token(token)
    uid = payload.get("sub")
    if uid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = await _fetch_user(db, UUID(uid))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ── FastAPI dependency ───────────────────────────────────────────────────────


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """FastAPI dependency that authenticates via Bearer JWT **or** X-API-Key header."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:]
        return await _resolve_user(token, db)

    if x_api_key:
        return await _resolve_user(x_api_key, db)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide Authorization: Bearer <token> or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Convenience alias for router dependencies
get_current_user_dependency = Depends(get_current_user)
