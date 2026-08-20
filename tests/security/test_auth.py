"""Tests for backend.security.auth — JWT creation, verification, and password hashing."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import jwt
import pytest

from backend.core.config import get_settings
from backend.security.auth import (
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)


settings = get_settings()


# ── Password Hashing ──────────────────────────────────────────────────────────


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        hashed = hash_password("securepass")
        assert verify_password("securepass", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("securepass")
        assert verify_password("wrongpass", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("samepass")
        h2 = hash_password("samepass")
        # bcrypt uses random salt, so hashes should differ
        assert h1 != h2

    def test_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True


# ── JWT Creation ──────────────────────────────────────────────────────────────


class TestCreateAccessToken:
    def test_creates_token(self):
        user_id = uuid4()
        token = create_access_token(user_id)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_token_contains_user_id(self):
        user_id = uuid4()
        token = create_access_token(user_id)
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        assert payload["sub"] == str(user_id)

    def test_custom_expiration(self):
        user_id = uuid4()
        token = create_access_token(user_id, expires_delta=timedelta(minutes=5))
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        assert "exp" in payload
        assert "iat" in payload


# ── JWT Verification ─────────────────────────────────────────────────────────


class TestVerifyToken:
    def test_valid_token(self):
        user_id = uuid4()
        token = create_access_token(user_id)
        payload = verify_token(token)
        assert payload["sub"] == str(user_id)

    def test_invalid_token(self):
        with pytest.raises(Exception):
            verify_token("completely.invalid.token")

    def test_tampered_token(self):
        user_id = uuid4()
        token = create_access_token(user_id)
        # Tamper with the token
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(Exception):
            verify_token(tampered)

    def test_wrong_secret(self):
        user_id = uuid4()
        payload = {
            "sub": str(user_id),
            "exp": 9999999999,
        }
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        with pytest.raises(Exception):
            verify_token(token)
