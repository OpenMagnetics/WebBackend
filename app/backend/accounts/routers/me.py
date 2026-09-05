"""Account self-service: settings sync, full data export, account deletion."""
import datetime
import io
import json
import re
import zipfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session as OrmSession

from ..db import get_db
from ..models import Design, DesignRevision, User, UserSettings
from ..security import current_user, verify_password

router = APIRouter(prefix="/me", tags=["me"])

MAX_SETTINGS_BYTES = 256 * 1024


class SettingsIn(BaseModel):
    settings: dict


# Profile settings document, version 2: one entry per SECTION (a store's
# roaming keys) with the timestamp of the device edit that produced it, so two
# devices merge per section (last write wins per section, never per whole
# document — a stale device cannot wipe another device's edits to a different
# section). A version-1 document (the whole settings store, pre-2026-09) is
# migrated on read into a single "settings" section stamped with the row's
# updated_at.
SECTION_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")


class SectionIn(BaseModel):
    values: dict
    updatedAt: str


def _as_v2(row: UserSettings | None) -> dict:
    if row is None:
        return {"version": 2, "sections": {}}
    doc = row.settings
    if isinstance(doc, dict) and isinstance(doc.get("sections"), dict):
        return doc
    return {
        "version": 2,
        "sections": {
            "settings": {"values": doc, "updatedAt": row.updated_at.isoformat()},
        },
    }


class DeleteAccountIn(BaseModel):
    password: str


@router.get("/settings")
def get_settings(user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    row = db.get(UserSettings, user.id)
    if row is None:
        return {"settings": None, "updated_at": None}
    return {"settings": _as_v2(row), "updated_at": row.updated_at.isoformat()}


@router.patch("/settings/sections/{name}")
def patch_settings_section(name: str, data: SectionIn,
                           user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    """Store one section if the client's edit is at least as new as the stored
    one; otherwise 409 with the stored section so the client applies it."""
    if not SECTION_NAME.match(name):
        raise HTTPException(status_code=422, detail="Invalid section name")
    row = db.get(UserSettings, user.id)
    doc = json.loads(json.dumps(_as_v2(row)))  # detached copy: JSONB mutation must be a new object
    existing = doc["sections"].get(name)
    if existing is not None and existing.get("updatedAt", "") > data.updatedAt:
        raise HTTPException(status_code=409, detail={"section": existing})
    doc["sections"][name] = {"values": data.values, "updatedAt": data.updatedAt}
    if len(json.dumps(doc, separators=(",", ":"))) > MAX_SETTINGS_BYTES:
        raise HTTPException(status_code=413, detail="Settings payload too large")
    if row is None:
        row = UserSettings(user_id=user.id, settings=doc)
        db.add(row)
    else:
        row.settings = doc
        row.updated_at = func.now()
    db.commit()
    row = db.get(UserSettings, user.id)
    return {"section": row.settings["sections"][name], "updated_at": row.updated_at.isoformat()}


@router.put("/settings")
def put_settings(data: SettingsIn, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    if len(json.dumps(data.settings, separators=(",", ":"))) > MAX_SETTINGS_BYTES:
        raise HTTPException(status_code=413, detail="Settings payload too large")
    row = db.get(UserSettings, user.id)
    if row is None:
        row = UserSettings(user_id=user.id, settings=data.settings)
        db.add(row)
    else:
        row.settings = data.settings
        row.updated_at = func.now()
    db.commit()
    row = db.get(UserSettings, user.id)
    return {"settings": row.settings, "updated_at": row.updated_at.isoformat()}


@router.get("/export")
def export_everything(user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    """Everything the account holds, as a zip of MAS JSON files — the GDPR
    export and the guarantee that user data is never stranded."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("profile.json", json.dumps({
            "email": user.email,
            "display_name": user.display_name,
            "created_at": user.created_at.isoformat(),
            "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }, indent=2))

        settings_row = db.get(UserSettings, user.id)
        if settings_row is not None:
            archive.writestr("settings.json", json.dumps(settings_row.settings, indent=2))

        designs = (db.query(Design)
                   .filter(Design.owner_user_id == user.id, Design.deleted_at.is_(None))
                   .all())
        for design in designs:
            latest = (db.query(DesignRevision)
                      .filter(DesignRevision.design_id == design.id)
                      .order_by(DesignRevision.revision.desc())
                      .first())
            if latest is None:
                raise HTTPException(status_code=500,
                                    detail=f"Design {design.id} has no revisions — data integrity error")
            safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in design.name).strip() or "design"
            archive.writestr(f"designs/{safe_name}-{design.id}.json", json.dumps(latest.mas, indent=2))

    buffer.seek(0)
    stamp = datetime.date.today().isoformat()
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="openmagnetics-export-{stamp}.zip"'},
    )


@router.delete("")
def delete_account(data: DeleteAccountIn, user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong password")
    # Hard delete: FK cascades remove sessions, email tokens, settings, designs
    # (and their revisions), inventory, share links and mounts.
    db.delete(user)
    db.commit()
    return {"status": "account_deleted"}
