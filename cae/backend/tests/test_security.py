"""Tests for app.utils.security — password hashing and JWT creation/verification."""
import uuid
from datetime import timedelta

import pytest
from jose import jwt

from app.config import settings
from app.utils import security


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
def test_password_hash_round_trips():
    hashed = security.get_password_hash("correct horse battery staple")
    assert security.verify_password("correct horse battery staple", hashed) is True


def test_password_hash_rejects_wrong_password():
    hashed = security.get_password_hash("right-password")
    assert security.verify_password("wrong-password", hashed) is False


def test_password_hash_is_salted():
    """Two hashes of the same password must differ (random salt) yet both verify."""
    h1 = security.get_password_hash("same-password")
    h2 = security.get_password_hash("same-password")
    assert h1 != h2
    assert security.verify_password("same-password", h1)
    assert security.verify_password("same-password", h2)


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------
def test_access_token_carries_subject_and_type():
    sub = str(uuid.uuid4())
    token = security.create_access_token({"sub": sub})

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == sub
    assert payload["type"] == "access"
    assert "exp" in payload


def test_refresh_token_is_typed_refresh():
    token = security.create_refresh_token({"sub": "abc"})

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["type"] == "refresh"


def test_access_token_honours_custom_expiry():
    short = security.create_access_token({"sub": "abc"}, expires_delta=timedelta(minutes=1))
    long = security.create_access_token({"sub": "abc"}, expires_delta=timedelta(hours=1))

    exp_short = jwt.decode(short, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])["exp"]
    exp_long = jwt.decode(long, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])["exp"]
    assert exp_long > exp_short


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------
def test_verify_token_returns_payload_for_valid_token():
    token = security.create_access_token({"sub": "abc"})
    payload = security.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "abc"


def test_verify_token_returns_none_for_garbage():
    assert security.verify_token("not-a-jwt") is None


def test_verify_token_returns_none_for_expired_token():
    expired = security.create_access_token({"sub": "abc"}, expires_delta=timedelta(seconds=-1))
    assert security.verify_token(expired) is None


def test_verify_token_returns_none_for_wrong_signature():
    forged = jwt.encode({"sub": "abc", "type": "access"}, "a-different-secret-key", algorithm="HS256")
    assert security.verify_token(forged) is None
