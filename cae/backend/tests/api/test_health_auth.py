"""Integration tests for health, login, token and the auth dependency stack."""
from tests.factories import COMPANY_ID, make_user


def test_health_is_public(api):
    resp = api.client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_login_returns_tokens_for_valid_credentials(api):
    api.seed_user(email="cfo@acme.co", password="hunter2-strong", role="cfo")

    resp = api.client.post("/api/v1/auth/login",
                           json={"email": "cfo@acme.co", "password": "hunter2-strong"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_rejects_wrong_password(api):
    api.seed_user(email="cfo@acme.co", password="hunter2-strong")

    resp = api.client.post("/api/v1/auth/login",
                           json={"email": "cfo@acme.co", "password": "wrong"})

    assert resp.status_code == 401


def test_login_rejects_unknown_email(api):
    resp = api.client.post("/api/v1/auth/login",
                           json={"email": "nobody@acme.co", "password": "x"})
    assert resp.status_code == 401


def test_me_returns_current_user(api):
    user = api.seed_user(email="me@acme.test", role="manager", company_id=COMPANY_ID)

    resp = api.auth_get("/api/v1/auth/me", user)

    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "me@acme.test"
    assert body["role"] == "manager"
    assert body["company_id"] == str(COMPANY_ID)


def test_protected_route_requires_a_token(api):
    resp = api.client.get("/api/v1/auth/me")
    assert resp.status_code == 403  # HTTPBearer: no credentials


def test_protected_route_rejects_garbage_token(api):
    resp = api.client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_refresh_token_cannot_be_used_as_access_token(api):
    """End-to-end check of the refresh-as-access guard via the HTTP layer."""
    from app.utils.security import create_refresh_token

    user = api.seed_user(email="r@acme.test")
    refresh = create_refresh_token({"sub": str(user.id)})

    resp = api.client.get("/api/v1/auth/me",
                          headers={"Authorization": f"Bearer {refresh}"})

    assert resp.status_code == 401
