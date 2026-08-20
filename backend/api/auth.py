"""Authentication endpoints — register & login with JWT."""

from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.models import User
from backend.db.session import get_db
from backend.security.auth import (
    create_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/auth")


# ── Request / response schemas ───────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _get_or_create_user(
    db: AsyncSession, email: str, password: str, name: str = ""
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()

    if existing:
        # Verify password for existing user
        if not verify_password(password, existing.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password.",
            )
        return existing

    # Create new user
    user = User(
        id=uuid4(),
        email=email,
        name=name or email.split("@")[0],
        hashed_password=hash_password(password),
    )
    db.add(user)
    await db.flush()
    return user


def _auth_response(user: User) -> dict:
    token = create_access_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name or user.email.split("@")[0],
        },
    }


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user or log in if email already exists."""
    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters.",
        )

    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Please sign in.",
        )

    user = User(
        id=uuid4(),
        email=body.email,
        name=body.name or body.email.split("@")[0],
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.flush()
    await db.commit()

    return _auth_response(user)


@router.post("/login")
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Log in with email and password."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return _auth_response(user)
