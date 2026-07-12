"""End-to-end tests for organizations (Phase 4): creation, invitations,
roles, org-owned designs/inventory with librarian lifecycle. Real DB,
self-cleaning via account deletion (org rows cascade from memberships;
orgs themselves are cleaned explicitly).
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
    auth_router, designs_router, inventory_router, me_router, orgs_router,
)

MAS_DATA_DIR = pathlib.Path(__file__).resolve().parents[2] / "MAS" / "data"


def make_app() -> FastAPI:
    app = FastAPI()
    for router in (auth_router, designs_router, inventory_router, me_router, orgs_router):
        app.include_router(router)
    return app


def make_user(tag):
    client = TestClient(make_app())
    email = f"pytest-org-{tag}-{uuid.uuid4().hex[:10]}@example.com"
    assert client.post("/auth/register", json={"email": email, "password": "pytest-password-1"}).status_code == 200
    return client, email


@pytest.fixture()
def acme():
    """Owner + org + an invited member and an invited viewer (accepted)."""
    owner, _ = make_user("owner")
    member, member_email = make_user("member")
    viewer, viewer_email = make_user("viewer")

    org = owner.post("/orgs", json={"name": "ACME Magnetics", "slug": f"acme-{uuid.uuid4().hex[:8]}"}).json()
    org_id = org["id"]

    for client, email, role in ((member, member_email, "member"), (viewer, viewer_email, "viewer")):
        invitation = owner.post(f"/orgs/{org_id}/invitations", json={"email": email, "role": role}).json()
        assert client.post(f"/orgs/invitations/{invitation['id']}/accept").status_code == 200

    yield {"owner": owner, "member": member, "viewer": viewer, "org_id": org_id}

    owner.delete(f"/orgs/{org_id}")
    for client in (owner, member, viewer):
        client.request("DELETE", "/me", json={"password": "pytest-password-1"})


@pytest.fixture()
def mas_document():
    from app.backend.accounts.mas_validation import validate_mas
    with open(pathlib.Path(__file__).resolve().parents[2] / "MAS" / "examples" / "00_debug.json") as f:
        document = json.load(f)
    assert not validate_mas(document), "00_debug should validate after the #189 refresh"
    return document


def test_org_creation_and_membership(acme):
    owner, member, org_id = acme["owner"], acme["member"], acme["org_id"]

    assert owner.get("/orgs").json()["orgs"][0]["my_role"] == "owner"
    assert member.get("/orgs").json()["orgs"][0]["my_role"] == "member"

    members = owner.get(f"/orgs/{org_id}/members").json()["members"]
    assert len(members) == 3 and not any(m["pending"] for m in members)

    # outsiders see nothing
    outsider, _ = make_user("outsider")
    assert outsider.get(f"/orgs/{org_id}/members").status_code == 404
    outsider.request("DELETE", "/me", json={"password": "pytest-password-1"})

    # member cannot invite (admin+), owner cannot demote the last owner
    assert member.post(f"/orgs/{org_id}/invitations",
                       json={"email": "x@example.com", "role": "member"}).status_code == 403
    own_id = next(m["id"] for m in members if m["role"] == "owner")
    assert owner.patch(f"/orgs/{org_id}/members/{own_id}", json={"role": "member"}).status_code == 409


def test_org_designs_roles(acme, mas_document):
    owner, member, viewer, org_id = acme["owner"], acme["member"], acme["viewer"], acme["org_id"]

    # member creates an org design; it is NOT in their personal list
    design = member.post(f"/designs?org={org_id}", json={"name": "Org trafo", "mas": mas_document}).json()
    assert member.get("/designs").json()["designs"] == []
    assert [d["name"] for d in member.get(f"/designs?org={org_id}").json()["designs"]] == ["Org trafo"]

    # every role can read it; viewer cannot modify
    assert viewer.get(f"/designs?org={org_id}").json()["designs"][0]["name"] == "Org trafo"
    assert viewer.get(f"/designs/{design['id']}").status_code == 200
    assert viewer.put(f"/designs/{design['id']}", json={"name": "nope"}).status_code == 403
    assert viewer.post(f"/designs?org={org_id}", json={"name": "x", "mas": mas_document}).status_code == 403

    # another member (the owner) can edit — org data does not belong to its creator
    assert owner.put(f"/designs/{design['id']}", json={"name": "Renamed by owner"}).status_code == 200

    # removing the creator keeps the design with the org
    members = owner.get(f"/orgs/{org_id}/members").json()["members"]
    member_id = next(m["id"] for m in members if m["role"] == "member")
    assert owner.delete(f"/orgs/{org_id}/members/{member_id}").status_code == 200
    assert member.get(f"/designs?org={org_id}").status_code == 404          # access gone
    assert [d["name"] for d in owner.get(f"/designs?org={org_id}").json()["designs"]] == ["Renamed by owner"]


def test_org_inventory_lifecycle(acme):
    owner, member, org_id = acme["owner"], acme["member"], acme["org_id"]
    with open(MAS_DATA_DIR / "wires.ndjson") as f:
        wire = json.loads(f.readline())

    # a member's new org part starts as a DRAFT (not blocked, not approved)
    part = member.post(f"/inventory?org={org_id}",
                       json={"part_type": "wire", "source": "private", "mas": wire}).json()
    assert part["lifecycle"] == "draft"

    # drafts do not reach the adviser context
    assert member.get("/inventory/context.json").json()["context"] == {}

    # member cannot approve; the owner (librarian rights) can
    assert member.patch(f"/inventory/{part['id']}", json={"lifecycle": "approved"}).status_code == 403
    assert owner.patch(f"/inventory/{part['id']}", json={"lifecycle": "approved"}).json()["lifecycle"] == "approved"

    # approved org parts now flow into EVERY member's adviser context
    context = member.get("/inventory/context.json").json()
    assert [w["name"] for w in context["context"]["wires"]] == [wire["name"]]

    # owner adds directly as approved (librarian+ shortcut)
    part2 = owner.post(f"/inventory?org={org_id}",
                       json={"part_type": "core", "source": "catalog", "catalog_ref": "Stock core"}).json()
    assert part2["lifecycle"] == "approved"
