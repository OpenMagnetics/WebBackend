"""Personal parts inventory: the approved-parts list the advisers can scope to.

Each row is one part owned by the user (org ownership arrives in Phase 4):
- source='catalog': a reference by MAS name to a public catalog part.
- source='private': a full MAS record (validated like designs — stored either
  way but quarantined with schema_valid semantics via the mas_valid flag in
  responses; adviser payloads only include clean parts).

Endpoints mirror the MAS ndjson data-file format for bulk import/export, and
/inventory/context.json returns the LibraryContext payload the frontend feeds
to library_context_load() / the load_* engine loaders.
"""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session as OrmSession

from ..db import get_db
from ..mas_validation import mas_spec_version, validate_mas_part
from ..models import InventoryPart, Membership, User
from ..orgs import ROLE_RANK, membership_of, resolve_owner
from ..security import current_user

router = APIRouter(prefix="/inventory", tags=["inventory"])

PART_TYPES = ("coreShape", "coreMaterial", "core", "bobbin", "wire")
# inventory_parts.part_type -> LibraryContext key (libMKF library_context_load)
CONTEXT_KEYS = {
    "coreShape": "coreShapes",
    "coreMaterial": "coreMaterials",
    "core": "cores",
    "bobbin": "bobbins",
    "wire": "wires",
}
MAX_PARTS_PER_OWNER = 1000
MAX_IMPORT_BYTES = 10 * 1024 * 1024


class PartIn(BaseModel):
    part_type: str
    name: str | None = None          # required for source='catalog'; derived from mas otherwise
    source: str
    catalog_ref: str | None = None
    mas: dict | None = None
    stock_qty: float | None = None
    order_code: str | None = None
    notes: str | None = None


class PartUpdateIn(BaseModel):
    mas: dict | None = None
    stock_qty: float | None = None
    order_code: str | None = None
    notes: str | None = None
    lifecycle: str | None = None     # org parts: librarian+ transitions


def _payload(part: InventoryPart) -> dict:
    return {
        "id": str(part.id),
        "part_type": part.part_type,
        "name": part.name,
        "source": part.source,
        "catalog_ref": part.catalog_ref,
        "mas": part.mas,
        "stock_qty": float(part.stock_qty) if part.stock_qty is not None else None,
        "order_code": part.order_code,
        "notes": part.notes,
        "lifecycle": part.lifecycle,
        "created_at": part.created_at.isoformat(),
        "updated_at": part.updated_at.isoformat(),
    }


def _validate_part_in(data: PartIn) -> tuple[str, list[str]]:
    """Returns (name, schema_errors). Raises 422 on structural nonsense."""
    if data.part_type not in PART_TYPES:
        raise HTTPException(status_code=422, detail=f"part_type must be one of {PART_TYPES}")
    if data.source == "catalog":
        name = (data.catalog_ref or data.name or "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="A catalog part needs catalog_ref (the public part name)")
        if data.mas is not None:
            raise HTTPException(status_code=422, detail="A catalog part must not carry a mas document")
        return name, []
    if data.source == "private":
        if data.mas is None:
            raise HTTPException(status_code=422, detail="A private part needs its full MAS record in 'mas'")
        name = str(data.mas.get("name") or data.name or "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="The MAS record has no 'name'")
        return name, validate_mas_part(data.part_type, data.mas)
    raise HTTPException(status_code=422, detail="source must be 'catalog' or 'private'")


def _own_parts(db: OrmSession, user: User, owner_org_id=None):
    owner_filter = (InventoryPart.owner_org_id == owner_org_id) if owner_org_id is not None \
        else (InventoryPart.owner_user_id == user.id)
    return db.query(InventoryPart).filter(owner_filter, InventoryPart.deleted_at.is_(None))


def _write_access(db: OrmSession, user: User, part: InventoryPart, need_librarian: bool = False):
    """Personal parts: free. Org parts: member+ edits metadata/drafts,
    librarian+ for lifecycle transitions and approved-part edits."""
    if part.owner_user_id == user.id:
        return
    if part.owner_org_id is not None:
        membership = membership_of(db, user.id, part.owner_org_id)
        minimum = "librarian" if need_librarian else "member"
        if membership is not None and ROLE_RANK[membership.role] >= ROLE_RANK[minimum]:
            return
        if membership is not None:
            raise HTTPException(status_code=403, detail=f"This action needs the '{minimum}' role or higher")
    raise HTTPException(status_code=404, detail="Part not found")


def _get_own_part(db: OrmSession, user: User, part_id: str) -> InventoryPart:
    try:
        key = uuid.UUID(part_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Part not found")
    part = (db.query(InventoryPart)
            .filter(InventoryPart.id == key, InventoryPart.deleted_at.is_(None))
            .one_or_none())
    if part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    if part.owner_user_id != user.id and (
            part.owner_org_id is None or membership_of(db, user.id, part.owner_org_id) is None):
        raise HTTPException(status_code=404, detail="Part not found")
    return part


def _check_quota(db: OrmSession, user: User, adding: int, owner_org_id=None):
    count = _own_parts(db, user, owner_org_id).count()
    if count + adding > MAX_PARTS_PER_OWNER:
        raise HTTPException(status_code=409,
                            detail=f"Inventory limit reached ({MAX_PARTS_PER_OWNER} parts)")


def _upsert_part(db: OrmSession, user: User, data: PartIn,
                 owner_user_id=None, owner_org_id=None, role=None) -> tuple[InventoryPart, list[str]]:
    name, schema_errors = _validate_part_in(data)
    if owner_user_id is None and owner_org_id is None:
        owner_user_id = user.id
    existing = (_own_parts(db, user, owner_org_id)
                .filter(InventoryPart.part_type == data.part_type, InventoryPart.name == name)
                .one_or_none())
    if existing is None:
        _check_quota(db, user, adding=1, owner_org_id=owner_org_id)
        # Personal parts skip the approval workflow; org parts start as
        # drafts unless a librarian+ adds them (OrCAD temp-part pattern:
        # members are never blocked, librarians promote later).
        if owner_org_id is None or (role is not None and ROLE_RANK[role] >= ROLE_RANK["librarian"]):
            lifecycle = "approved"
        else:
            lifecycle = "draft"
        existing = InventoryPart(
            owner_user_id=owner_user_id,
            owner_org_id=owner_org_id,
            part_type=data.part_type,
            name=name,
            source=data.source,
            created_by=user.id,
            lifecycle=lifecycle,
        )
        db.add(existing)
    existing.source = data.source
    existing.catalog_ref = name if data.source == "catalog" else None
    existing.mas = data.mas
    existing.mas_version = mas_spec_version() if data.source == "private" else None
    existing.stock_qty = data.stock_qty
    existing.order_code = data.order_code
    existing.notes = data.notes
    existing.updated_at = func.now()
    return existing, schema_errors


@router.get("")
def list_parts(org: str | None = None, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    _, owner_org_id, _role = resolve_owner(db, user, org, minimum="viewer")
    parts = _own_parts(db, user, owner_org_id).order_by(InventoryPart.part_type, InventoryPart.name).all()
    return {"parts": [_payload(p) for p in parts]}


@router.post("")
def create_part(data: PartIn, org: str | None = None,
                user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    owner_user_id, owner_org_id, role = resolve_owner(db, user, org, minimum="member")
    part, schema_errors = _upsert_part(db, user, data, owner_user_id, owner_org_id, role)
    db.commit()
    db.refresh(part)
    payload = _payload(part)
    payload["schema_errors"] = schema_errors
    return payload


@router.patch("/{part_id}")
def update_part(part_id: str, data: PartUpdateIn,
                user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    part = _get_own_part(db, user, part_id)
    # Editing an APPROVED org part or transitioning lifecycle needs librarian+;
    # draft edits need member+.
    need_librarian = data.lifecycle is not None or (
        part.owner_org_id is not None and part.lifecycle == "approved" and data.mas is not None)
    _write_access(db, user, part, need_librarian=need_librarian)
    schema_errors = []
    if data.lifecycle is not None:
        if data.lifecycle not in ("draft", "approved", "deprecated", "obsolete"):
            raise HTTPException(status_code=422, detail="Unknown lifecycle state")
        part.lifecycle = data.lifecycle
    if data.mas is not None:
        if part.source != "private":
            raise HTTPException(status_code=422, detail="Only private parts carry a MAS record")
        schema_errors = validate_mas_part(part.part_type, data.mas)
        part.mas = data.mas
        part.mas_version = mas_spec_version()
    if data.stock_qty is not None:
        part.stock_qty = data.stock_qty
    if data.order_code is not None:
        part.order_code = data.order_code
    if data.notes is not None:
        part.notes = data.notes
    part.updated_at = func.now()
    db.commit()
    db.refresh(part)
    payload = _payload(part)
    payload["schema_errors"] = schema_errors
    return payload


@router.delete("/{part_id}")
def delete_part(part_id: str, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    part = _get_own_part(db, user, part_id)
    _write_access(db, user, part, need_librarian=(part.owner_org_id is not None
                                                  and part.lifecycle == "approved"))
    part.deleted_at = func.now()
    db.commit()
    return {"status": "deleted"}


@router.post("/import")
async def import_ndjson(request: Request, part_type: str, org: str | None = None,
                        user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    owner_user_id, owner_org_id, role = resolve_owner(db, user, org, minimum="member")
    """Bulk import: request body is MAS ndjson (one record per line), exactly
    the format Core Studio exports and the MAS data files use."""
    if part_type not in PART_TYPES:
        raise HTTPException(status_code=422, detail=f"part_type must be one of {PART_TYPES}")
    body = await request.body()
    if len(body) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=413, detail="Import exceeds the 10 MB limit")
    lines = [line for line in body.decode("utf-8").splitlines() if line.strip()]
    if not lines:
        raise HTTPException(status_code=422, detail="Empty import")
    _check_quota(db, user, adding=len(lines), owner_org_id=owner_org_id)

    imported, errors = [], []
    for index, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"line {index}: not valid JSON ({error})")
            continue
        data = PartIn(part_type=part_type, source="private", mas=record)
        try:
            part, schema_errors = _upsert_part(db, user, data, owner_user_id, owner_org_id, role)
            imported.append({"name": part.name, "schema_errors": schema_errors})
        except HTTPException as error:
            errors.append(f"line {index}: {error.detail}")
    db.commit()
    return {"imported": imported, "errors": errors}


@router.get("/export.ndjson", response_class=PlainTextResponse)
def export_ndjson(part_type: str, org: str | None = None,
                  user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    if part_type not in PART_TYPES:
        raise HTTPException(status_code=422, detail=f"part_type must be one of {PART_TYPES}")
    _, owner_org_id, _role = resolve_owner(db, user, org, minimum="viewer")
    parts = (_own_parts(db, user, owner_org_id)
             .filter(InventoryPart.part_type == part_type, InventoryPart.source == "private")
             .order_by(InventoryPart.name)
             .all())
    return "\n".join(json.dumps(p.mas) for p in parts if p.mas is not None)


@router.get("/context.json")
def context_json(user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    """The engine-facing payload: private parts grouped by LibraryContext key,
    plus catalog references the frontend resolves against the embedded catalog.
    Only 'approved' parts are included (personal parts always are; the
    lifecycle matters once org inventories arrive). Inventories the user has
    MOUNTED via share links are folded in, so advisers can design with them."""
    from ..models import InventoryMount, ShareLink

    parts = list(_own_parts(db, user)
                 .filter(InventoryPart.lifecycle == "approved")
                 .all())
    org_ids = [org_id for (org_id,) in
               (db.query(Membership.org_id)
                .filter(Membership.user_id == user.id,
                        Membership.accepted_at.isnot(None),
                        Membership.revoked_at.is_(None))
                .all())]
    if org_ids:
        parts += (db.query(InventoryPart)
                  .filter(InventoryPart.owner_org_id.in_(org_ids),
                          InventoryPart.deleted_at.is_(None),
                          InventoryPart.lifecycle == "approved")
                  .all())
    mounted_owner_ids = [owner_id for (owner_id,) in
                         (db.query(ShareLink.owner_user_id)
                          .join(InventoryMount, InventoryMount.share_link_id == ShareLink.id)
                          .filter(InventoryMount.mounter_user_id == user.id,
                                  InventoryMount.removed_at.is_(None),
                                  ShareLink.revoked_at.is_(None))
                          .all()) if owner_id is not None]
    if mounted_owner_ids:
        parts += (db.query(InventoryPart)
                  .filter(InventoryPart.owner_user_id.in_(mounted_owner_ids),
                          InventoryPart.deleted_at.is_(None),
                          InventoryPart.lifecycle == "approved")
                  .all())
    private = {key: [] for key in CONTEXT_KEYS.values()}
    catalog_refs = {key: [] for key in CONTEXT_KEYS.values()}
    for part in parts:
        key = CONTEXT_KEYS[part.part_type]
        if part.source == "private" and part.mas is not None:
            private[key].append(part.mas)
        elif part.source == "catalog":
            catalog_refs[key].append(part.catalog_ref)
    return {
        "context": {key: records for key, records in private.items() if records},
        "catalogRefs": {key: names for key, names in catalog_refs.items() if names},
    }
