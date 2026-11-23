"""Tests for app.utils.rbac — JWT-backed authentication and role enforcement.

The dependencies are async callables; we invoke them directly (rather than via a
full TestClient) with a constructed credentials object and a real DB session.
"""
import uuid
from datetime import timedelta

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.utils import rbac
from app.utils.security import create_access_token, create_refresh_token
from tests.factories import make_user


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _persist(db, user):
    db.add(user)
    db.commit()
    return user


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------
async def test_valid_access_token_resolves_user(db):
    user = _persist(db, make_user(role="auditor"))
    token = create_access_token({"sub": str(user.id)})

    resolved = await rbac.get_current_user(credentials=_creds(token), db=db)

    assert resolved.id == user.id


async def test_refresh_token_is_rejected_as_access(db):
    """Security guard: a refresh token must not authenticate API requests."""
    user = _persist(db, make_user())
    refresh = create_refresh_token({"sub": str(user.id)})

    with pytest.raises(HTTPException) as exc:
        await rbac.get_current_user(credentials=_creds(refresh), db=db)
    assert exc.value.status_code == 401
    assert "access token required" in exc.value.detail.lower()


async def test_expired_token_is_rejected(db):
    user = _persist(db, make_user())
    expired = create_access_token({"sub": str(user.id)}, expires_delta=timedelta(seconds=-1))

    with pytest.raises(HTTPException) as exc:
        await rbac.get_current_user(credentials=_creds(expired), db=db)
    assert exc.value.status_code == 401


async def test_garbage_token_is_rejected(db):
    with pytest.raises(HTTPException) as exc:
        await rbac.get_current_user(credentials=_creds("not-a-jwt"), db=db)
    assert exc.value.status_code == 401


async def test_token_without_sub_is_rejected(db):
    token = create_access_token({"foo": "bar"})  # no 'sub'

    with pytest.raises(HTTPException) as exc:
        await rbac.get_current_user(credentials=_creds(token), db=db)
    assert exc.value.status_code == 401


async def test_unknown_user_is_rejected(db):
    token = create_access_token({"sub": str(uuid.uuid4())})  # no such user row

    with pytest.raises(HTTPException) as exc:
        await rbac.get_current_user(credentials=_creds(token), db=db)
    assert exc.value.status_code == 401


async def test_inactive_user_is_rejected(db):
    user = _persist(db, make_user(is_active=False))
    token = create_access_token({"sub": str(user.id)})

    with pytest.raises(HTTPException) as exc:
        await rbac.get_current_user(credentials=_creds(token), db=db)
    assert exc.value.status_code == 401


# ---------------------------------------------------------------------------
# require_roles / convenience dependencies
# ---------------------------------------------------------------------------
async def test_require_roles_allows_permitted_role(db):
    user = make_user(role="partner")
    checker = rbac.require_roles("super_admin", "partner")

    assert await checker(current_user=user) is user


async def test_require_roles_denies_other_role(db):
    user = make_user(role="auditor")
    checker = rbac.require_roles("super_admin", "partner")

    with pytest.raises(HTTPException) as exc:
        await checker(current_user=user)
    assert exc.value.status_code == 403


@pytest.mark.parametrize(
    "dependency,role,allowed",
    [
        (rbac.require_super_admin, "super_admin", True),
        (rbac.require_super_admin, "partner", False),
        (rbac.require_partner, "partner", True),
        (rbac.require_partner, "super_admin", True),
        (rbac.require_partner, "auditor", False),
        (rbac.require_auditor, "auditor", True),
        (rbac.require_auditor, "cfo", False),
        (rbac.require_management, "cfo", True),
        (rbac.require_management, "auditor", False),
    ],
)
async def test_convenience_dependencies_enforce_roles(dependency, role, allowed):
    user = make_user(role=role)
    if allowed:
        assert await dependency(current_user=user) is user
    else:
        with pytest.raises(HTTPException) as exc:
            await dependency(current_user=user)
        assert exc.value.status_code == 403
