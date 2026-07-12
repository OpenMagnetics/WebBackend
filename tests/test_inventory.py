"""End-to-end tests for the personal inventory (Phase 2), in the style of
test_accounts.py: real DB via OM_DB_*, self-cleaning through account deletion.
"""
import json
import os
import pathlib
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("OM_ENV", "development")

from app.backend.accounts.routers import auth_router, inventory_router, me_router  # noqa: E402

MAS_DATA_DIR = pathlib.Path(__file__).resolve().parents[2] / "MAS" / "data"


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(inventory_router)
    app.include_router(me_router)
    return app


@pytest.fixture()
def client():
    return TestClient(make_app())


@pytest.fixture()
def account(client):
    email = f"pytest-inv-{uuid.uuid4().hex[:12]}@example.com"
    password = "pytest-password-1"
    response = client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    yield {"email": email, "password": password}
    client.request("DELETE", "/me", json={"password": password})


def data_record(filename):
    with open(MAS_DATA_DIR / filename) as f:
        return json.loads(f.readline())


def test_inventory_crud_catalog_and_private(client, account):
    # anonymous rejected
    assert TestClient(make_app()).get("/inventory").status_code == 401

    # catalog reference part
    response = client.post("/inventory", json={
        "part_type": "core", "source": "catalog", "catalog_ref": "ETD 34/17/11 - 3C97 - Gapped 0.5 mm",
        "stock_qty": 120, "order_code": "WH-ETD34-05",
    })
    assert response.status_code == 200, response.text
    catalog_part = response.json()
    assert catalog_part["source"] == "catalog" and catalog_part["mas"] is None
    assert catalog_part["schema_errors"] == []

    # private part: a real wire record from the MAS data files
    wire = data_record("wires.ndjson")
    response = client.post("/inventory", json={"part_type": "wire", "source": "private", "mas": wire})
    assert response.status_code == 200, response.text
    private_part = response.json()
    assert private_part["name"] == wire["name"]
    assert private_part["schema_errors"] == []

    # listing shows both
    parts = client.get("/inventory").json()["parts"]
    assert len(parts) == 2

    # upsert by (part_type, name): same wire again updates, no duplicate
    response = client.post("/inventory", json={
        "part_type": "wire", "source": "private", "mas": wire, "notes": "reorder point 500m",
    })
    assert response.status_code == 200
    parts = client.get("/inventory").json()["parts"]
    assert len(parts) == 2
    assert next(p for p in parts if p["part_type"] == "wire")["notes"] == "reorder point 500m"

    # patch metadata
    response = client.patch(f"/inventory/{private_part['id']}", json={"stock_qty": 42})
    assert response.status_code == 200 and response.json()["stock_qty"] == 42

    # invalid private part is stored but flagged
    response = client.post("/inventory", json={
        "part_type": "coreMaterial", "source": "private", "mas": {"name": "garbage-material", "not": "valid"},
    })
    assert response.status_code == 200
    assert response.json()["schema_errors"]

    # structural nonsense is rejected outright
    assert client.post("/inventory", json={
        "part_type": "flux-capacitor", "source": "private", "mas": {}}).status_code == 422
    assert client.post("/inventory", json={
        "part_type": "core", "source": "catalog"}).status_code == 422
    assert client.post("/inventory", json={
        "part_type": "core", "source": "private"}).status_code == 422

    # delete
    assert client.delete(f"/inventory/{catalog_part['id']}").status_code == 200
    assert len(client.get("/inventory").json()["parts"]) == 2  # wire + garbage material remain


def test_ndjson_import_export_roundtrip(client, account):
    with open(MAS_DATA_DIR / "core_shapes.ndjson") as f:
        lines = [f.readline().strip() for _ in range(3)]
    body = "\n".join(lines) + "\nnot json at all\n"

    response = client.post("/inventory/import?part_type=coreShape",
                           content=body.encode(), headers={"Content-Type": "application/x-ndjson"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert len(result["imported"]) == 3
    assert all(not r["schema_errors"] for r in result["imported"])
    assert len(result["errors"]) == 1 and "line 4" in result["errors"][0]

    exported = client.get("/inventory/export.ndjson?part_type=coreShape").text.splitlines()
    assert len(exported) == 3
    assert {json.loads(l)["name"] for l in exported} == {json.loads(l)["name"] for l in lines}


def test_context_json_groups_by_engine_key(client, account):
    wire = data_record("wires.ndjson")
    material = data_record("core_materials.ndjson")
    client.post("/inventory", json={"part_type": "wire", "source": "private", "mas": wire})
    client.post("/inventory", json={"part_type": "coreMaterial", "source": "private", "mas": material})
    client.post("/inventory", json={"part_type": "core", "source": "catalog", "catalog_ref": "Some Stock Core"})

    payload = client.get("/inventory/context.json").json()
    assert [w["name"] for w in payload["context"]["wires"]] == [wire["name"]]
    assert [m["name"] for m in payload["context"]["coreMaterials"]] == [material["name"]]
    assert payload["catalogRefs"]["cores"] == ["Some Stock Core"]
    assert "cores" not in payload["context"]
