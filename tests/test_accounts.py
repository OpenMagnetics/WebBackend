"""End-to-end tests for the accounts feature (auth, designs, settings, export,
deletion), in the style of test_telemetry.py: they run against the real
database configured by OM_DB_* and clean up after themselves (account deletion
cascades everything the tests created).

Run:  ./.venv/bin/pytest tests/test_accounts.py -q
"""
import json
import os
import pathlib
import uuid
import zipfile
import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("OM_ENV", "development")  # plain non-Secure cookie for TestClient

from app.backend.accounts.routers import auth_router, designs_router, me_router  # noqa: E402

MAS_EXAMPLE_DIR = pathlib.Path(__file__).resolve().parents[2] / "MAS" / "examples"


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(designs_router)
    app.include_router(me_router)
    return app


@pytest.fixture()
def client():
    return TestClient(make_app())


@pytest.fixture()
def mas_document():
    """A schema-valid MAS document, built from the 00_debug example. The stored
    example predates the removal of core 'magneticCircuit' from the schema
    (stale-examples issue reported to MAS via ABT), so strip that key; the
    result must validate — fail loudly if it drifts again."""
    from app.backend.accounts.mas_validation import validate_mas

    with open(MAS_EXAMPLE_DIR / "00_debug.json") as f:
        document = json.load(f)
    document["magnetic"]["core"]["functionalDescription"].pop("magneticCircuit", None)
    errors = validate_mas(document)
    if errors:
        raise RuntimeError(f"00_debug.json (minus magneticCircuit) no longer validates: {errors[:3]}")
    return document


@pytest.fixture()
def account(client):
    """A registered, logged-in account. Deleted (with cascades) on teardown."""
    email = f"pytest-{uuid.uuid4().hex[:12]}@example.com"
    password = "pytest-password-1"
    response = client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    yield {"email": email, "password": password, "user": response.json()}
    client.request("DELETE", "/me", json={"password": password})


def test_register_login_logout_me(client):
    email = f"pytest-{uuid.uuid4().hex[:12]}@example.com"
    password = "pytest-password-1"

    # check_email before registration
    assert client.post("/auth/check_email", json={"email": email}).json() == {"exists": False}

    # register sets a session cookie and /auth/me works
    response = client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    assert response.json()["email"] == email
    assert response.json()["display_name"] == email.split("@")[0]
    assert client.get("/auth/me").status_code == 200

    try:
        assert client.post("/auth/check_email", json={"email": email}).json() == {"exists": True}

        # duplicate register refused
        assert client.post("/auth/register", json={"email": email, "password": password}).status_code == 409

        # logout kills the session
        assert client.post("/auth/logout").status_code == 200
        assert client.get("/auth/me").status_code == 401

        # wrong password refused, right password logs in
        assert client.post("/auth/login", json={"email": email, "password": "wrong-password"}).status_code == 401
        assert client.post("/auth/login", json={"email": email, "password": password}).status_code == 200
        assert client.get("/auth/me").status_code == 200
    finally:
        client.request("DELETE", "/me", json={"password": password})


def test_register_rejects_weak_input(client):
    assert client.post("/auth/register", json={"email": "not-an-email", "password": "long-enough-1"}).status_code == 422
    assert client.post("/auth/register",
                       json={"email": f"pytest-{uuid.uuid4().hex[:8]}@example.com", "password": "short"}).status_code == 422


def test_designs_crud_revisions_and_conflict(client, account, mas_document):
    # anonymous is rejected
    anonymous = TestClient(make_app())
    assert anonymous.get("/designs").status_code == 401

    # create — valid document is stored with schema_valid true and no errors
    response = client.post("/designs", json={"name": "Test transformer", "mas": mas_document})
    assert response.status_code == 200, response.text
    design = response.json()
    assert design["version"] == 1 and design["revisions"] == 1
    assert design["schema_valid"] is True and design["schema_errors"] == []

    # list
    listing = client.get("/designs").json()["designs"]
    assert len(listing) == 1 and listing[0]["name"] == "Test transformer"

    # get returns the document byte-identical
    fetched = client.get(f"/designs/{design['id']}").json()
    assert fetched["mas"] == mas_document
    assert fetched["mas_version"]

    # identical save is a no-op (with correct If-Match)
    response = client.put(f"/designs/{design['id']}",
                          headers={"If-Match": "1"}, json={"mas": mas_document})
    assert response.status_code == 200 and response.json()["unchanged"] is True
    assert response.json()["version"] == 1

    # a real change bumps version + revision
    changed = json.loads(json.dumps(mas_document))
    changed["magnetic"]["manufacturerInfo"] = (changed["magnetic"].get("manufacturerInfo") or {})
    changed["magnetic"]["manufacturerInfo"]["reference"] = "pytest-changed-reference"
    response = client.put(f"/designs/{design['id']}",
                          headers={"If-Match": "1"}, json={"mas": changed})
    assert response.status_code == 200, response.text
    assert response.json()["version"] == 2 and response.json()["unchanged"] is False

    # stale If-Match conflicts with the current version in the payload
    response = client.put(f"/designs/{design['id']}",
                          headers={"If-Match": "1"}, json={"mas": mas_document})
    assert response.status_code == 409
    assert response.json()["detail"]["current_version"] == 2

    # missing If-Match when saving is refused
    assert client.put(f"/designs/{design['id']}", json={"mas": mas_document}).status_code == 428

    # revisions listed newest-first, both fetchable
    revisions = client.get(f"/designs/{design['id']}/revisions").json()["revisions"]
    assert [r["revision"] for r in revisions] == [2, 1]
    assert client.get(f"/designs/{design['id']}/revisions/1").json()["mas"] == mas_document
    assert client.get(f"/designs/{design['id']}/revisions/2").json()["mas"] == changed

    # rename without mas needs no If-Match
    response = client.put(f"/designs/{design['id']}", json={"name": "Renamed transformer"})
    assert response.status_code == 200 and response.json()["name"] == "Renamed transformer"

    # delete hides it
    assert client.delete(f"/designs/{design['id']}").status_code == 200
    assert client.get(f"/designs/{design['id']}").status_code == 404
    assert client.get("/designs").json()["designs"] == []


def test_design_flags_invalid_mas(client, account):
    # Invalid documents are stored (quarantined) but explicitly flagged, with
    # the exact validation errors surfaced in the response and the listing.
    response = client.post("/designs", json={"name": "Broken", "mas": {"not": "a mas document"}})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema_valid"] is False
    assert body["schema_errors"]

    listing = client.get("/designs").json()["designs"]
    assert listing[0]["schema_valid"] is False
    fetched = client.get(f"/designs/{body['id']}").json()
    assert fetched["schema_valid"] is False and fetched["mas"] == {"not": "a mas document"}


def test_settings_roundtrip(client, account):
    assert client.get("/me/settings").json()["settings"] is None
    payload = {"adviserSettings": {"useOnlyCoresInStock": True}, "theme": "dark"}
    response = client.put("/me/settings", json={"settings": payload})
    assert response.status_code == 200 and response.json()["settings"] == payload
    assert client.get("/me/settings").json()["settings"] == payload


def test_change_password_invalidates_other_sessions(client, account):
    other = TestClient(make_app())
    assert other.post("/auth/login",
                      json={"email": account["email"], "password": account["password"]}).status_code == 200
    assert other.get("/auth/me").status_code == 200

    response = client.post("/auth/change_password", json={
        "current_password": account["password"],
        "new_password": "pytest-password-2",
    })
    assert response.status_code == 200
    account["password"] = "pytest-password-2"

    assert other.get("/auth/me").status_code == 401       # other session killed
    assert client.get("/auth/me").status_code == 200      # this one survives


def test_export_zip(client, account, mas_document):
    client.post("/designs", json={"name": "Export me", "mas": mas_document})
    response = client.get("/me/export")
    assert response.status_code == 200
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    names = archive.namelist()
    assert "profile.json" in names
    assert any(n.startswith("designs/Export me-") for n in names)


def test_delete_account_cascades(client, mas_document):
    email = f"pytest-{uuid.uuid4().hex[:12]}@example.com"
    password = "pytest-password-1"
    assert client.post("/auth/register", json={"email": email, "password": password}).status_code == 200
    client.post("/designs", json={"name": "Doomed", "mas": mas_document})

    assert client.request("DELETE", "/me", json={"password": "wrong-password"}).status_code == 401
    assert client.request("DELETE", "/me", json={"password": password}).status_code == 200
    assert client.get("/auth/me").status_code == 401
    assert client.post("/auth/check_email", json={"email": email}).json() == {"exists": False}


def test_password_reset_without_smtp_is_503(client):
    if any(os.getenv(v) for v in ("OM_SMTP_HOST",)):
        pytest.skip("SMTP is configured in this environment")
    response = client.post("/auth/request_password_reset", json={"email": "whoever@example.com"})
    assert response.status_code == 503
