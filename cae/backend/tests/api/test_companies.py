"""Integration tests for /companies — tenant scoping and role gates."""
import uuid

from app.models.tenant import Company
from tests.factories import TENANT_ID

OTHER_TENANT = uuid.UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")


def _company(tenant_id=TENANT_ID, **kw):
    defaults = dict(id=uuid.uuid4(), tenant_id=tenant_id, name="ACME Pvt Ltd")
    defaults.update(kw)
    return Company(**defaults)


def test_list_companies_is_scoped_to_tenant(api):
    user = api.seed_user(role="auditor")
    api.add(_company(name="Mine"))
    api.add(_company(tenant_id=OTHER_TENANT, name="Theirs"))

    resp = api.auth_get("/api/v1/companies", user)

    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert names == ["Mine"]


def test_list_companies_excludes_inactive(api):
    user = api.seed_user(role="manager")
    api.add(_company(name="Active"))
    api.add(_company(name="Archived", is_active=False))

    resp = api.auth_get("/api/v1/companies", user)

    assert [c["name"] for c in resp.json()] == ["Active"]


def test_list_companies_forbidden_for_client_user(api):
    user = api.seed_user(role="client_user")

    resp = api.auth_get("/api/v1/companies", user)

    assert resp.status_code == 403


def test_create_company_as_partner(api):
    user = api.seed_user(role="partner")

    resp = api.auth_post("/api/v1/companies", user,
                         json={"name": "NewCo", "gstin": "27AAAAA0000A1Z5"})

    assert resp.status_code == 201
    assert resp.json()["name"] == "NewCo"
    # persisted under the caller's tenant
    assert api.db.query(Company).filter(Company.name == "NewCo").one().tenant_id == TENANT_ID


def test_create_company_forbidden_for_auditor(api):
    user = api.seed_user(role="auditor")

    resp = api.auth_post("/api/v1/companies", user, json={"name": "NewCo"})

    assert resp.status_code == 403


def test_get_company_in_own_tenant(api):
    user = api.seed_user(role="manager")
    company = api.add(_company(name="Mine"))

    resp = api.auth_get(f"/api/v1/companies/{company.id}", user)

    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Mine"
    assert body["id"] == str(company.id)


def test_get_company_404_when_missing(api):
    user = api.seed_user(role="partner")

    resp = api.auth_get(f"/api/v1/companies/{uuid.uuid4()}", user)

    assert resp.status_code == 404


def test_get_company_in_other_tenant_is_not_found(api):
    user = api.seed_user(role="partner")
    foreign = api.add(_company(tenant_id=OTHER_TENANT, name="Theirs"))

    resp = api.auth_get(f"/api/v1/companies/{foreign.id}", user)

    assert resp.status_code == 404
