"""Share links (Phase 3): capability URLs for designs and inventories.

- A design link exposes one design read-only (latest revision, or pinned).
- An inventory link exposes the owner's approved parts; a logged-in user can
  MOUNT it, which folds those parts into their /inventory/context.json so the
  advisers can design with them ("public + mine + theirs").
- Possession of the token IS the permission; owners can revoke at any time.
  Public GETs are unauthenticated and cheap (single JSONB read).
"""
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session as OrmSession

from ..db import get_db
from ..models import Design, DesignRevision, InventoryMount, InventoryPart, ShareLink, User
from ..security import current_user

router = APIRouter(tags=["shares"])

MAX_LINKS_PER_USER = 200


class ShareDesignIn(BaseModel):
    pinned_revision: int | None = None


def _link_payload(link: ShareLink, db: OrmSession) -> dict:
    payload = {
        "id": str(link.id),
        "token": link.token,
        "kind": link.kind,
        "created_at": link.created_at.isoformat(),
        "visit_count": link.visit_count,
        "pinned_revision": link.pinned_revision,
    }
    if link.kind == "design" and link.design_id is not None:
        design = db.get(Design, link.design_id)
        payload["design_name"] = design.name if design is not None else None
    return payload


def _count_links(db: OrmSession, user: User) -> int:
    return (db.query(func.count(ShareLink.id))
            .filter(ShareLink.created_by == user.id, ShareLink.revoked_at.is_(None))
            .scalar())


@router.post("/designs/{design_id}/share")
def share_design(design_id: str, data: ShareDesignIn,
                 user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    try:
        key = uuid.UUID(design_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Design not found")
    design = (db.query(Design)
              .filter(Design.id == key, Design.owner_user_id == user.id, Design.deleted_at.is_(None))
              .one_or_none())
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")
    if data.pinned_revision is not None:
        if db.get(DesignRevision, (design.id, data.pinned_revision)) is None:
            raise HTTPException(status_code=404, detail="Revision not found")
    if _count_links(db, user) >= MAX_LINKS_PER_USER:
        raise HTTPException(status_code=409, detail=f"Share-link limit reached ({MAX_LINKS_PER_USER})")

    link = ShareLink(
        token=secrets.token_urlsafe(16),
        kind="design",
        design_id=design.id,
        pinned_revision=data.pinned_revision,
        created_by=user.id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return _link_payload(link, db)


@router.post("/inventory/share")
def share_inventory(user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    if _count_links(db, user) >= MAX_LINKS_PER_USER:
        raise HTTPException(status_code=409, detail=f"Share-link limit reached ({MAX_LINKS_PER_USER})")
    link = ShareLink(
        token=secrets.token_urlsafe(16),
        kind="inventory",
        owner_user_id=user.id,
        created_by=user.id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return _link_payload(link, db)


@router.get("/me/shares")
def list_my_shares(user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    links = (db.query(ShareLink)
             .filter(ShareLink.created_by == user.id, ShareLink.revoked_at.is_(None))
             .order_by(ShareLink.created_at.desc())
             .all())
    return {"shares": [_link_payload(link, db) for link in links]}


@router.delete("/shares/{link_id}")
def revoke_share(link_id: str, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    try:
        key = uuid.UUID(link_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Share link not found")
    link = (db.query(ShareLink)
            .filter(ShareLink.id == key, ShareLink.created_by == user.id, ShareLink.revoked_at.is_(None))
            .one_or_none())
    if link is None:
        raise HTTPException(status_code=404, detail="Share link not found")
    link.revoked_at = func.now()
    db.commit()
    return {"status": "revoked"}


def _live_link(db: OrmSession, token: str, kind: str) -> ShareLink:
    link = (db.query(ShareLink)
            .filter(ShareLink.token == token, ShareLink.kind == kind, ShareLink.revoked_at.is_(None))
            .one_or_none())
    if link is None:
        raise HTTPException(status_code=404, detail="This share link does not exist or was revoked")
    link.visit_count = ShareLink.visit_count + 1
    db.commit()
    db.refresh(link)
    return link


@router.get("/share/d/{token}")
def open_shared_design(token: str, response: Response, db: OrmSession = Depends(get_db)):
    link = _live_link(db, token, "design")
    design = db.get(Design, link.design_id)
    if design is None or design.deleted_at is not None:
        raise HTTPException(status_code=404, detail="The shared design no longer exists")
    if link.pinned_revision is not None:
        revision = db.get(DesignRevision, (design.id, link.pinned_revision))
        response.headers["Cache-Control"] = "public, max-age=86400"
    else:
        revision = (db.query(DesignRevision)
                    .filter(DesignRevision.design_id == design.id)
                    .order_by(DesignRevision.revision.desc())
                    .first())
        response.headers["Cache-Control"] = "public, max-age=60"
    if revision is None:
        raise HTTPException(status_code=404, detail="The shared design no longer exists")
    return {
        "name": design.name,
        "revision": revision.revision,
        "mas_version": revision.mas_version,
        "saved_at": revision.saved_at.isoformat(),
        "mas": revision.mas,
    }


@router.get("/share/i/{token}")
def open_shared_inventory(token: str, response: Response, db: OrmSession = Depends(get_db)):
    link = _live_link(db, token, "inventory")
    owner = db.get(User, link.owner_user_id) if link.owner_user_id is not None else None
    if owner is None or owner.deleted_at is not None:
        raise HTTPException(status_code=404, detail="The shared inventory no longer exists")
    parts = (db.query(InventoryPart)
             .filter(InventoryPart.owner_user_id == owner.id,
                     InventoryPart.deleted_at.is_(None),
                     InventoryPart.lifecycle == "approved")
             .order_by(InventoryPart.part_type, InventoryPart.name)
             .all())
    response.headers["Cache-Control"] = "public, max-age=60"
    return {
        "owner": owner.display_name,
        "parts": [{
            "part_type": p.part_type,
            "name": p.name,
            "source": p.source,
            "catalog_ref": p.catalog_ref,
            "mas": p.mas,
            "stock_qty": float(p.stock_qty) if p.stock_qty is not None else None,
            "order_code": p.order_code,
        } for p in parts],
    }


@router.post("/share/i/{token}/mount")
def mount_shared_inventory(token: str, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    link = _live_link(db, token, "inventory")
    if link.owner_user_id == user.id:
        raise HTTPException(status_code=422, detail="This is your own inventory")
    existing = (db.query(InventoryMount)
                .filter(InventoryMount.share_link_id == link.id,
                        InventoryMount.mounter_user_id == user.id,
                        InventoryMount.removed_at.is_(None))
                .one_or_none())
    if existing is None:
        db.add(InventoryMount(share_link_id=link.id, mounter_user_id=user.id))
        db.commit()
    return {"status": "mounted"}


@router.delete("/share/i/{token}/mount")
def unmount_shared_inventory(token: str, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    link = (db.query(ShareLink)
            .filter(ShareLink.token == token, ShareLink.kind == "inventory")
            .one_or_none())
    if link is None:
        raise HTTPException(status_code=404, detail="Share link not found")
    mount = (db.query(InventoryMount)
             .filter(InventoryMount.share_link_id == link.id,
                     InventoryMount.mounter_user_id == user.id,
                     InventoryMount.removed_at.is_(None))
             .one_or_none())
    if mount is None:
        raise HTTPException(status_code=404, detail="Not mounted")
    mount.removed_at = func.now()
    db.commit()
    return {"status": "unmounted"}


@router.get("/me/mounts")
def list_my_mounts(user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    rows = (db.query(InventoryMount, ShareLink, User)
            .join(ShareLink, ShareLink.id == InventoryMount.share_link_id)
            .outerjoin(User, User.id == ShareLink.owner_user_id)
            .filter(InventoryMount.mounter_user_id == user.id, InventoryMount.removed_at.is_(None))
            .all())
    return {"mounts": [{
        "token": link.token,
        "owner": owner.display_name if owner is not None else None,
        "revoked": link.revoked_at is not None,
        "mounted_at": mount.created_at.isoformat(),
    } for mount, link, owner in rows]}
