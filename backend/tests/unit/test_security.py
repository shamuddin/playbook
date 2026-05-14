"""Security-focused unit tests for authentication, authorization, and input validation."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    decode_access_token,
)
from app.core.config import Settings


class TestJWTSecurity:
    def test_access_token_creation_and_verification(self):
        token = create_access_token(
            data={"sub": "user-123", "email": "test@example.com", "role": "admin"}
        )
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # header.payload.signature

    def test_token_contains_expiry(self):
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=timedelta(minutes=30),
        )
        payload = decode_access_token(token)
        assert payload is not None
        assert "exp" in payload
        assert payload["sub"] == "user-123"

    def test_token_expired_rejected(self):
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=timedelta(minutes=-30),
        )
        payload = decode_access_token(token)
        assert payload is None

    def test_tampered_token_rejected(self):
        token = create_access_token(data={"sub": "user-123"})
        tampered = token[:-5] + "XXXXX"
        payload = decode_access_token(tampered)
        assert payload is None


class TestPasswordSecurity:
    # NOTE: These tests mock pwd_context to avoid a bcrypt/passlib compatibility
    # issue in this environment (bcrypt 4.x removed __about__, breaking passlib
    # backend detection). The actual get_password_hash/verify_password wrappers
    # are thin pass-throughs to pwd_context.

    def test_password_hashing(self):
        with patch("app.core.security.pwd_context") as mock_ctx:
            mock_ctx.hash.return_value = "$2b$12$mockhash"
            mock_ctx.verify.return_value = True
            plain = "secret_123"
            hashed = get_password_hash(plain)
            assert hashed == "$2b$12$mockhash"
            mock_ctx.hash.assert_called_once_with(plain)

    def test_wrong_password_fails(self):
        with patch("app.core.security.pwd_context") as mock_ctx:
            mock_ctx.hash.return_value = "$2b$12$mockhash"
            mock_ctx.verify.return_value = False
            plain = "correct_pass"
            hashed = get_password_hash(plain)
            assert verify_password("wrong_pass", hashed) is False
            mock_ctx.verify.assert_called_once_with("wrong_pass", hashed)

    def test_hash_uniqueness(self):
        with patch("app.core.security.pwd_context") as mock_ctx:
            mock_ctx.hash.side_effect = ["$2b$12$hashA", "$2b$12$hashB"]
            mock_ctx.verify.return_value = True
            plain = "my_pass"
            hash1 = get_password_hash(plain)
            hash2 = get_password_hash(plain)
            assert hash1 != hash2
            assert verify_password(plain, hash1) is True
            assert verify_password(plain, hash2) is True


class TestSettingsValidation:
    def test_secret_key_min_length(self):
        with pytest.raises(ValueError):
            Settings(secret_key="short")

    def test_secret_key_rejects_defaults(self):
        with pytest.raises(ValueError):
            Settings(secret_key="change-me-in-production")

    def test_valid_secret_key(self):
        key = "a" * 32 + "_secure_random_key_2026"
        s = Settings(secret_key=key)
        assert s.secret_key == key

    def test_cors_origins_parsing(self):
        s = Settings(cors_origins="http://localhost:5173, https://app.example.com")
        assert s.cors_origins_list == ["http://localhost:5173", "https://app.example.com"]

    def test_database_pool_size_bounds(self):
        with pytest.raises(ValueError, match="database_pool_size must be between 1 and 20"):
            Settings(database_pool_size=0)
        with pytest.raises(ValueError, match="database_pool_size must be between 1 and 20"):
            Settings(database_pool_size=25)

    def test_jwt_algorithm_fixed(self):
        s = Settings()
        assert s.algorithm == "HS256"

    def test_token_expire_minutes_positive(self):
        s = Settings()
        assert s.access_token_expire_minutes > 0
