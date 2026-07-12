"""Organization membership helpers shared by the org-aware routers.

Roles (proposal v2 §4): owner > admin > librarian > member > viewer.
- owner: everything, incl. deleting the org; the last owner is protected.
- admin: manage members/invitations.
- librarian: approve/deprecate inventory parts.
- member: create/edit designs, author draft parts.
- viewer: read-only.
"""
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session as OrmSession

from .models import Membership, Organization

ROLE_RANK = {"viewer": 0, "member": 1, "librarian": 2, "admin": 3, "owner": 4}


def parse_uuid(value: str, what: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"{what} not found")


def get_org(db: OrmSession, org_id) -> Organization:
    org = db.get(Organization, org_id)
    if org is None or org.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


def membership_of(db: OrmSession, user_id, org_id) -> Membership | None:
    return (db.query(Membership)
            .filter(Membership.org_id == org_id,
                    Membership.user_id == user_id,
                    Membership.accepted_at.isnot(None),
                    Membership.revoked_at.is_(None))
            .one_or_none())


def require_role(db: OrmSession, user_id, org_id, minimum: str) -> Membership:
    membership = membership_of(db, user_id, org_id)
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if ROLE_RANK[membership.role] < ROLE_RANK[minimum]:
        raise HTTPException(status_code=403, detail=f"This action needs the '{minimum}' role or higher")
    return membership


def resolve_owner(db: OrmSession, user, org_param: str | None, minimum: str = "member"):
    """Routers accept ?org=<id> to act on an organization instead of the
    personal space. Returns (owner_user_id, owner_org_id, role) with exactly
    one owner id set; role is None for the personal space."""
    if org_param is None or org_param == "":
        return user.id, None, None
    org_id = parse_uuid(org_param, "Organization")
    get_org(db, org_id)
    membership = require_role(db, user.id, org_id, minimum)
    return None, org_id, membership.role
