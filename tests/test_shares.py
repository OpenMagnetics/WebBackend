"""End-to-end tests for share links (Phase 3), same style as the other
account suites: real DB, self-cleaning via account deletion.
"""
import json
import os
import pathlib
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("OM_ENV", "development")

from app.backend.accounts.routers import (  # noqa: E402
    auth_router, designs_router, inventory_router, me_router, shares_router,
)

MAS_DATA_DIR = pathlib.Path(__file__).resolve().parents[2] / "MAS" / "data"


def make_app() -> FastAPI:
    app = FastAPI()
    for router in (auth_router, designs_router, inventory_router, me_router, shares_router):
        app.include_router(router)
    return app


def register(client, tag):
    email = f"pytest-share-{tag}-{uuid.uuid4().hex[:10]}@example.com"
    response = client.post("/auth/register", json={"email": email, "password": "pytest-password-1"})
    assert response.status_code == 200, response.text
    return email


@pytest.fixture()
def alice():
    client = TestClient(make_app())
    register(client, "alice")
    yield client
    client.request("DELETE", "/me", json={"password": "pytest-password-1"})


@pytest.fixture()
def bob():
    client = TestClient(make_app())
    register(client, "bob")
    yield client
    client.request("DELETE", "/me", json={"password": "pytest-password-1"})


@pytest.fixture()
def mas_document():
    from app.backend.accounts.mas_validation import validate_mas
    with open(pathlib.Path(__file__).resolve().parents[2] / "MAS" / "examples" / "00_debug.json") as f:
        document = json.load(f)
    document["magnetic"]["core"]["functionalDescription"].pop("magneticCircuit", None)
    assert not validate_mas(document)
    return document


def test_design_share_lifecycle(alice, mas_document):
    design = alice.post("/designs", json={"name": "Shared trafo", "mas": mas_document}).json()

    link = alice.post(f"/designs/{design['id']}/share", json={}).json()
    assert link["kind"] == "design" and link["design_name"] == "Shared trafo"
    token = link["token"]

    # anyone (no session) can open it
    anonymous = TestClient(make_app())
    shared = anonymous.get(f"/share/d/{token}")
    assert shared.status_code == 200, shared.text
    assert shared.json()["name"] == "Shared trafo"
    assert shared.json()["mas"] == mas_document
    assert "max-age" in shared.headers.get("cache-control", "")

    # visit counter moved
    listed = alice.get("/me/shares").json()["shares"]
    assert listed[0]["visit_count"] >= 1

    # revoke kills it
    assert alice.delete(f"/shares/{link['id']}").status_code == 200
    assert anonymous.get(f"/share/d/{token}").status_code == 404


def test_design_share_pinned_revision(alice, mas_document):
    design = alice.post("/designs", json={"name": "Pinned", "mas": mas_document}).json()
    changed = json.loads(json.dumps(mas_document))
    changed["magnetic"]["manufacturerInfo"] = changed["magnetic"].get("manufacturerInfo") or {}
    changed["magnetic"]["manufacturerInfo"]["reference"] = "pytest-v2"
    alice.put(f"/designs/{design['id']}", headers={"If-Match": "1"}, json={"mas": changed})

    pinned = alice.post(f"/designs/{design['id']}/share", json={"pinned_revision": 1}).json()
    latest = alice.post(f"/designs/{design['id']}/share", json={}).json()

    anonymous = TestClient(make_app())
    assert anonymous.get(f"/share/d/{pinned['token']}").json()["mas"] == mas_document
    assert anonymous.get(f"/share/d/{latest['token']}").json()["mas"] == changed

    # nonexistent revision refused
    assert alice.post(f"/designs/{design['id']}/share", json={"pinned_revision": 99}).status_code == 404


def test_inventory_share_and_mount(alice, bob):
    with open(MAS_DATA_DIR / "wires.ndjson") as f:
        wire = json.loads(f.readline())
    alice.post("/inventory", json={"part_type": "wire", "source": "private", "mas": wire})
    alice.post("/inventory", json={"part_type": "core", "source": "catalog", "catalog_ref": "Some Core"})

    token = alice.post("/inventory/share").json()["token"]

    # public view
    anonymous = TestClient(make_app())
    shared = anonymous.get(f"/share/i/{token}").json()
    assert len(shared["parts"]) == 2
    assert shared["owner"].startswith("pytest-share-alice")

    # anonymous cannot mount; the owner cannot mount their own
    assert anonymous.post(f"/share/i/{token}/mount").status_code == 401
    assert alice.post(f"/share/i/{token}/mount").status_code == 422

    # bob mounts: alice's parts appear in bob's engine context
    assert bob.post(f"/share/i/{token}/mount").status_code == 200
    context = bob.get("/inventory/context.json").json()
    assert [w["name"] for w in context["context"]["wires"]] == [wire["name"]]
    assert context["catalogRefs"]["cores"] == ["Some Core"]
    assert bob.get("/me/mounts").json()["mounts"][0]["token"] == token

    # unmount clears it
    assert bob.request("DELETE", f"/share/i/{token}/mount").status_code == 200
    context = bob.get("/inventory/context.json").json()
    assert context["context"] == {} and context["catalogRefs"] == {}

    # remount, then alice revokes -> bob's context is clean again
    bob.post(f"/share/i/{token}/mount")
    link_id = alice.get("/me/shares").json()["shares"][0]["id"]
    alice.delete(f"/shares/{link_id}")
    assert anonymous.get(f"/share/i/{token}").status_code == 404
    context = bob.get("/inventory/context.json").json()
    assert context["context"] == {} and context["catalogRefs"] == {}
