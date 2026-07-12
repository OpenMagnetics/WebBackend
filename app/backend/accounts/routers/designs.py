"""My Designs: envelope + append-only revisions around untouched MAS documents.

- Validate-on-write against the MAS schemas. Documents are stored either way,
  but flagged: schema_valid=false rows are explicit quarantine, and the exact
  validation errors are returned in the response (schema_errors) so the client
  can show them. Nothing is rejected or silently fixed — rejecting outright is
  not viable today because even canonical MAS examples trip a known PEAS
  constraint bug (negativePeak maximum:0 vs. DC-biased waveforms, see ABT).
- Optimistic concurrency: PUT requires If-Match: <version>; a stale version
  gets 409 with the current version so the client can offer reload/overwrite.
- Saving a byte-identical document is a no-op (no new revision).
"""
import hashlib
import json
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session as OrmSession

from ..db import get_db
from ..mas_validation import mas_spec_version, validate_mas
from ..models import Design, DesignRevision, User
from ..security import current_user

router = APIRouter(prefix="/designs", tags=["designs"])

MAX_DESIGNS_PER_USER = 100
MAX_REVISIONS_PER_DESIGN = 50
MAX_DESIGN_BYTES = 2 * 1024 * 1024


class DesignIn(BaseModel):
    name: str
    mas: dict
    engine_version: str | None = None


class DesignUpdateIn(BaseModel):
    name: str | None = None
    mas: dict | None = None
    engine_version: str | None = None


def _canonical_hash(mas: dict) -> str:
    canonical = json.dumps(mas, sort_keys=True, separators=(",", ":"))
    if len(canonical) > MAX_DESIGN_BYTES:
        raise HTTPException(status_code=413, detail=f"Design exceeds the {MAX_DESIGN_BYTES // (1024 * 1024)} MB limit")
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _latest_flags(db: OrmSession, design_ids: list) -> dict:
    """schema_valid of the latest revision, per design id."""
    if not design_ids:
        return {}
    rows = (db.query(DesignRevision.design_id, DesignRevision.schema_valid)
            .filter(DesignRevision.design_id.in_(design_ids))
            .distinct(DesignRevision.design_id)
            .order_by(DesignRevision.design_id, DesignRevision.revision.desc())
            .all())
    return {design_id: schema_valid for design_id, schema_valid in rows}


def _envelope(design: Design, revisions: int | None = None) -> dict:
    payload = {
        "id": str(design.id),
        "name": design.name,
        "version": design.version,
        "created_at": design.created_at.isoformat(),
        "updated_at": design.updated_at.isoformat(),
    }
    if revisions is not None:
        payload["revisions"] = revisions
    return payload


def _get_own_design(db: OrmSession, user: User, design_id: str) -> Design:
    try:
        key = uuid.UUID(design_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Design not found")
    design = (db.query(Design)
              .filter(Design.id == key, Design.owner_user_id == user.id, Design.deleted_at.is_(None))
              .one_or_none())
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")
    return design


def _latest_revision(db: OrmSession, design: Design) -> DesignRevision:
    revision = (db.query(DesignRevision)
                .filter(DesignRevision.design_id == design.id)
                .order_by(DesignRevision.revision.desc())
                .first())
    if revision is None:
        raise HTTPException(status_code=500, detail=f"Design {design.id} has no revisions — data integrity error")
    return revision


@router.get("")
def list_designs(user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    rows = (db.query(Design, func.count(DesignRevision.revision))
            .outerjoin(DesignRevision, DesignRevision.design_id == Design.id)
            .filter(Design.owner_user_id == user.id, Design.deleted_at.is_(None))
            .group_by(Design.id)
            .order_by(Design.updated_at.desc())
            .all())
    flags = _latest_flags(db, [design.id for design, _ in rows])
    designs = []
    for design, revisions in rows:
        payload = _envelope(design, revisions)
        payload["schema_valid"] = flags.get(design.id)
        designs.append(payload)
    return {"designs": designs}


@router.post("")
def create_design(data: DesignIn, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Design name must not be empty")
    count = (db.query(func.count(Design.id))
             .filter(Design.owner_user_id == user.id, Design.deleted_at.is_(None))
             .scalar())
    if count >= MAX_DESIGNS_PER_USER:
        raise HTTPException(status_code=409, detail=f"Design limit reached ({MAX_DESIGNS_PER_USER}). Delete old designs first.")

    mas_hash = _canonical_hash(data.mas)
    schema_errors = validate_mas(data.mas)

    design = Design(owner_user_id=user.id, name=name, created_by=user.id, version=1)
    db.add(design)
    db.flush()
    db.add(DesignRevision(
        design_id=design.id,
        revision=1,
        mas=data.mas,
        mas_hash=mas_hash,
        mas_version=mas_spec_version(),
        engine_version=data.engine_version,
        schema_valid=not schema_errors,
        saved_by=user.id,
    ))
    db.commit()
    db.refresh(design)
    payload = _envelope(design, revisions=1)
    payload["schema_valid"] = not schema_errors
    payload["schema_errors"] = schema_errors
    return payload


@router.get("/{design_id}")
def get_design(design_id: str, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    design = _get_own_design(db, user, design_id)
    revision = _latest_revision(db, design)
    payload = _envelope(design)
    payload.update({
        "mas": revision.mas,
        "revision": revision.revision,
        "mas_version": revision.mas_version,
        "engine_version": revision.engine_version,
        "schema_valid": revision.schema_valid,
    })
    return payload


@router.put("/{design_id}")
def update_design(design_id: str, data: DesignUpdateIn,
                  if_match: int | None = Header(default=None, alias="If-Match"),
                  user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    design = _get_own_design(db, user, design_id)

    if data.name is not None:
        name = data.name.strip()
        if not name:
            raise HTTPException(status_code=422, detail="Design name must not be empty")
        design.name = name

    unchanged = False
    schema_errors = []
    if data.mas is not None:
        if if_match is None:
            raise HTTPException(status_code=428, detail="If-Match header with the design version is required to save")
        if if_match != design.version:
            raise HTTPException(status_code=409, detail={
                "message": "Design was modified elsewhere",
                "current_version": design.version,
            })
        mas_hash = _canonical_hash(data.mas)
        latest = _latest_revision(db, design)
        if latest.mas_hash == mas_hash:
            unchanged = True
        else:
            schema_errors = validate_mas(data.mas)
            if latest.revision >= MAX_REVISIONS_PER_DESIGN:
                # Revision history is a rolling window: drop the oldest.
                oldest = (db.query(DesignRevision)
                          .filter(DesignRevision.design_id == design.id)
                          .order_by(DesignRevision.revision.asc())
                          .first())
                db.delete(oldest)
            db.add(DesignRevision(
                design_id=design.id,
                revision=latest.revision + 1,
                mas=data.mas,
                mas_hash=mas_hash,
                mas_version=mas_spec_version(),
                engine_version=data.engine_version,
                schema_valid=not schema_errors,
                saved_by=user.id,
            ))
            design.version = design.version + 1

    design.updated_at = func.now()
    db.commit()
    db.refresh(design)
    payload = _envelope(design)
    payload["unchanged"] = unchanged
    payload["schema_errors"] = schema_errors
    return payload


@router.delete("/{design_id}")
def delete_design(design_id: str, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    design = _get_own_design(db, user, design_id)
    design.deleted_at = func.now()
    db.commit()
    return {"status": "deleted"}


@router.get("/{design_id}/revisions")
def list_revisions(design_id: str, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    design = _get_own_design(db, user, design_id)
    rows = (db.query(DesignRevision)
            .filter(DesignRevision.design_id == design.id)
            .order_by(DesignRevision.revision.desc())
            .all())
    return {"revisions": [{
        "revision": row.revision,
        "saved_at": row.saved_at.isoformat(),
        "mas_version": row.mas_version,
        "engine_version": row.engine_version,
    } for row in rows]}


@router.get("/{design_id}/revisions/{revision}")
def get_revision(design_id: str, revision: int,
                 user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    design = _get_own_design(db, user, design_id)
    row = db.get(DesignRevision, (design.id, revision))
    if row is None:
        raise HTTPException(status_code=404, detail="Revision not found")
    return {
        "revision": row.revision,
        "saved_at": row.saved_at.isoformat(),
        "mas_version": row.mas_version,
        "engine_version": row.engine_version,
        "mas": row.mas,
    }
