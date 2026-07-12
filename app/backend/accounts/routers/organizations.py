"""Organizations (Phase 4): company accounts with employees and roles.

Invitations are email-first (myTI pattern): an admin invites an address, the
pending membership row itself is the capability (unguessable uuid4 id mailed
as a link); whoever holds the link and is signed in accepts it. The company
owns its designs/inventory — revoking a member never touches org data.
"""
import datetime
import re

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session as OrmSession

from .. import emailer
from ..db import get_db
from ..models import Membership, Organization, User
from ..orgs import ROLE_RANK, get_org, membership_of, parse_uuid, require_role
from ..ratelimit import limit
from ..security import current_user

router = APIRouter(prefix="/orgs", tags=["orgs"])

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$")
MAX_MEMBERS = 25
MAX_ORGS_PER_USER = 10
INVITABLE_ROLES = ("admin", "librarian", "member", "viewer")


class OrgIn(BaseModel):
    name: str
    slug: str


class InviteIn(BaseModel):
    email: str
    role: str


class RoleIn(BaseModel):
    role: str


def _org_payload(org: Organization, role: str | None = None) -> dict:
    return {"id": str(org.id), "slug": org.slug, "name": org.name,
            "created_at": org.created_at.isoformat(), "my_role": role}


def _member_payload(membership: Membership, db: OrmSession) -> dict:
    user = db.get(User, membership.user_id) if membership.user_id is not None else None
    return {
        "id": str(membership.id),
        "role": membership.role,
        "display_name": user.display_name if user is not None else None,
        "email": user.email if user is not None else membership.invited_email,
        "pending": membership.accepted_at is None,
    }


def _live_members(db: OrmSession, org_id):
    return (db.query(Membership)
            .filter(Membership.org_id == org_id, Membership.revoked_at.is_(None))
            .order_by(Membership.created_at))


def _count_owners(db: OrmSession, org_id) -> int:
    return (_live_members(db, org_id)
            .filter(Membership.role == "owner", Membership.accepted_at.isnot(None))
            .count())


@router.get("")
def my_orgs(user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    rows = (db.query(Organization, Membership)
            .join(Membership, Membership.org_id == Organization.id)
            .filter(Membership.user_id == user.id,
                    Membership.accepted_at.isnot(None),
                    Membership.revoked_at.is_(None),
                    Organization.deleted_at.is_(None))
            .order_by(Organization.name)
            .all())
    return {"orgs": [_org_payload(org, membership.role) for org, membership in rows]}


@router.post("", dependencies=[Depends(limit("org_create", 10, 3600))])
def create_org(data: OrgIn, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    name = data.name.strip()
    slug = data.slug.strip().lower()
    if not name:
        raise HTTPException(status_code=422, detail="Organization name must not be empty")
    if not SLUG_RE.match(slug):
        raise HTTPException(status_code=422, detail="Slug must be 3-40 chars of a-z, 0-9 and dashes")
    mine = (db.query(func.count(Membership.id))
            .filter(Membership.user_id == user.id, Membership.revoked_at.is_(None))
            .scalar())
    if mine >= MAX_ORGS_PER_USER:
        raise HTTPException(status_code=409, detail=f"Organization limit reached ({MAX_ORGS_PER_USER})")
    if db.query(Organization).filter(Organization.slug == slug).one_or_none() is not None:
        raise HTTPException(status_code=409, detail="This slug is taken")

    org = Organization(slug=slug, name=name)
    db.add(org)
    db.flush()
    db.add(Membership(org_id=org.id, user_id=user.id, role="owner",
                      invited_by=user.id, accepted_at=func.now()))
    db.commit()
    db.refresh(org)
    return _org_payload(org, "owner")


@router.delete("/{org_id}")
def delete_org(org_id: str, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    """Owner-only soft delete. Org designs/inventory stay in the DB (soft-
    deleted org hides them everywhere); a future restore stays possible."""
    key = parse_uuid(org_id, "Organization")
    org = get_org(db, key)
    require_role(db, user.id, key, "owner")
    org.deleted_at = func.now()
    db.commit()
    return {"status": "deleted"}


@router.get("/{org_id}/members")
def list_members(org_id: str, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    key = parse_uuid(org_id, "Organization")
    require_role(db, user.id, key, "viewer")
    return {"members": [_member_payload(m, db) for m in _live_members(db, key).all()]}


@router.post("/{org_id}/invitations", dependencies=[Depends(limit("org_invite", 20, 3600))])
def invite(org_id: str, data: InviteIn, background_tasks: BackgroundTasks,
           user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    key = parse_uuid(org_id, "Organization")
    org = get_org(db, key)
    require_role(db, user.id, key, "admin")
    email = data.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=422, detail="Not a valid email address")
    if data.role not in INVITABLE_ROLES:
        raise HTTPException(status_code=422, detail=f"Role must be one of {INVITABLE_ROLES}")
    if _live_members(db, key).count() >= MAX_MEMBERS:
        raise HTTPException(status_code=409, detail=f"Member limit reached ({MAX_MEMBERS})")
    existing_user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).one_or_none()
    if existing_user is not None and membership_of(db, existing_user.id, key) is not None:
        raise HTTPException(status_code=409, detail="Already a member")
    pending = (_live_members(db, key)
               .filter(Membership.invited_email == email, Membership.accepted_at.is_(None))
               .one_or_none())
    if pending is not None:
        raise HTTPException(status_code=409, detail="Already invited — the invitation is pending")

    membership = Membership(org_id=key, invited_email=email, role=data.role, invited_by=user.id)
    db.add(membership)
    db.commit()
    db.refresh(membership)

    if emailer.smtp_configured():
        link = f"{emailer.public_url()}/accept_invite?id={membership.id}"
        background_tasks.add_task(
            emailer.send_email_background, email,
            f"You are invited to {org.name} on OpenMagnetics",
            f"{user.display_name} invited you to join '{org.name}' on OpenMagnetics as {data.role}.\n\n"
            f"Accept here (sign in or create a free account first):\n{link}\n\n"
            f"If you were not expecting this, ignore this email.")
    return _member_payload(membership, db)


@router.get("/invitations/{membership_id}")
def view_invitation(membership_id: str, db: OrmSession = Depends(get_db)):
    key = parse_uuid(membership_id, "Invitation")
    membership = db.get(Membership, key)
    if membership is None or membership.accepted_at is not None or membership.revoked_at is not None:
        raise HTTPException(status_code=404, detail="Invitation not found or already used")
    org = get_org(db, membership.org_id)
    return {"org_name": org.name, "role": membership.role, "invited_email": membership.invited_email}


@router.post("/invitations/{membership_id}/accept")
def accept_invitation(membership_id: str, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    key = parse_uuid(membership_id, "Invitation")
    membership = db.get(Membership, key)
    if membership is None or membership.accepted_at is not None or membership.revoked_at is not None:
        raise HTTPException(status_code=404, detail="Invitation not found or already used")
    org = get_org(db, membership.org_id)
    if membership_of(db, user.id, org.id) is not None:
        raise HTTPException(status_code=409, detail="Already a member")
    membership.user_id = user.id
    membership.accepted_at = func.now()
    db.commit()
    return {"status": "accepted", "org": _org_payload(org, membership.role)}


@router.patch("/{org_id}/members/{membership_id}")
def change_role(org_id: str, membership_id: str, data: RoleIn,
                user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    org_key = parse_uuid(org_id, "Organization")
    require_role(db, user.id, org_key, "admin")
    if data.role not in ROLE_RANK:
        raise HTTPException(status_code=422, detail="Unknown role")
    membership = db.get(Membership, parse_uuid(membership_id, "Member"))
    if membership is None or membership.org_id != org_key or membership.revoked_at is not None:
        raise HTTPException(status_code=404, detail="Member not found")
    if membership.role == "owner" and data.role != "owner" and _count_owners(db, org_key) <= 1:
        raise HTTPException(status_code=409, detail="An organization needs at least one owner")
    if data.role == "owner":
        require_role(db, user.id, org_key, "owner")
    membership.role = data.role
    db.commit()
    return _member_payload(membership, db)


@router.delete("/{org_id}/members/{membership_id}")
def remove_member(org_id: str, membership_id: str,
                  user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    org_key = parse_uuid(org_id, "Organization")
    membership = db.get(Membership, parse_uuid(membership_id, "Member"))
    if membership is None or membership.org_id != org_key or membership.revoked_at is not None:
        raise HTTPException(status_code=404, detail="Member not found")
    if membership.user_id == user.id:
        require_role(db, user.id, org_key, "viewer")   # leaving yourself
    else:
        require_role(db, user.id, org_key, "admin")
    if (membership.role == "owner" and membership.accepted_at is not None
            and _count_owners(db, org_key) <= 1):
        raise HTTPException(status_code=409, detail="An organization needs at least one owner")
    membership.revoked_at = func.now()
    db.commit()
    return {"status": "removed"}
