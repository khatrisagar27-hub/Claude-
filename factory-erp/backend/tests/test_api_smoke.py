def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_register_login_and_create_plant(client):
    register = client.post(
        "/api/v1/auth/register",
        json={"name": "Admin", "email": "admin@example.com", "password": "secret123", "role": "admin"},
    )
    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "secret123"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"

    create_plant = client.post(
        "/api/v1/plants", json={"code": "PL1", "name": "Plant One"}, headers=headers
    )
    assert create_plant.status_code == 201
    plant_id = create_plant.json()["id"]

    list_plants = client.get("/api/v1/plants", headers=headers)
    assert list_plants.status_code == 200
    assert any(p["id"] == plant_id for p in list_plants.json())


def test_endpoints_require_auth(client):
    resp = client.get("/api/v1/plants")
    assert resp.status_code == 401


def test_wrong_password_rejected(client):
    client.post(
        "/api/v1/auth/register",
        json={"name": "A", "email": "a@example.com", "password": "correct-pass", "role": "operator"},
    )
    resp = client.post(
        "/api/v1/auth/login", json={"email": "a@example.com", "password": "wrong-pass"}
    )
    assert resp.status_code == 401


def test_reorder_alert_via_api(client):
    register = client.post(
        "/api/v1/auth/register",
        json={"name": "A", "email": "b@example.com", "password": "secret123", "role": "admin"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": "b@example.com", "password": "secret123"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    plant_id = client.post("/api/v1/plants", json={"code": "P2", "name": "P2"}, headers=headers).json()["id"]
    product = client.post(
        "/api/v1/stock/products",
        json={
            "plant_id": plant_id,
            "sku": "S1",
            "name": "Steel Sheet",
            "reorder_level": 100,
        },
        headers=headers,
    ).json()

    alerts = client.get(f"/api/v1/analytics/stock/reorder-alerts/{plant_id}", headers=headers)
    assert alerts.status_code == 200
    assert any(a["product_id"] == product["id"] for a in alerts.json())
