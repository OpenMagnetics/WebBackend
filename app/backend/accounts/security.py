"""Password hashing, session tokens and the session cookie.

- Argon2id via pwdlib (passlib is unmaintained).
- Sessions are server-side rows; the browser only holds an opaque random token
  in an HttpOnly cookie. The DB stores sha256(token), never the token itself.
- Cookie is `__Host-`-prefixed + Secure in production (requires HTTPS, no
  Domain attribute); plain-named and non-Secure in development so
  http://localhost keeps working. Rolling ~1 year expiry.
"""
import datetime
import hashlib
import os
import secrets

from fastapi import Depends, HTTPException, Request, Response
from pwdlib import PasswordHash
from sqlalchemy.orm import Session as OrmSession

from .db import get_db
from .models import AuthSession, User

_password_hash = PasswordHash.recommended()

SESSION_LIFETIME = datetime.timedelta(days=365)
# Extend the session row at most once a day to avoid a write per request.
SESSION_TOUCH_INTERVAL = datetime.timedelta(hours=24)


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def is_production():
    return os.getenv("OM_ENV", "production") == "production"


def cookie_name():
    return "__Host-om_session" if is_production() else "om_session"


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hash.verify(password, password_hash)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: OrmSession, user: User, user_agent: str | None) -> str:
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(
        token_hash=_hash_token(token),
        user_id=user.id,
        expires_at=_utcnow() + SESSION_LIFETIME,
        last_seen_at=_utcnow(),
        user_agent=(user_agent or "")[:400],
    ))
    db.commit()
    return token


def set_session_cookie(response: Response, token: str):
    response.set_cookie(
        key=cookie_name(),
        value=token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=is_production(),
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response):
    response.delete_cookie(key=cookie_name(), path="/")


def destroy_session(db: OrmSession, request: Request):
    token = request.cookies.get(cookie_name())
    if token:
        db.query(AuthSession).filter(AuthSession.token_hash == _hash_token(token)).delete()
        db.commit()


def destroy_other_sessions(db: OrmSession, user: User, request: Request):
    """Kill every session of the user except the one making the request."""
    token = request.cookies.get(cookie_name())
    query = db.query(AuthSession).filter(AuthSession.user_id == user.id)
    if token:
        query = query.filter(AuthSession.token_hash != _hash_token(token))
    query.delete()
    db.commit()


def _lookup_user(request: Request, db: OrmSession):
    token = request.cookies.get(cookie_name())
    if not token:
        return None
    now = _utcnow()
    session = db.get(AuthSession, _hash_token(token))
    if session is None or session.expires_at < now:
        return None
    user = db.get(User, session.user_id)
    if user is None or user.disabled_at is not None or user.deleted_at is not None:
        return None
    if session.last_seen_at is None or now - session.last_seen_at > SESSION_TOUCH_INTERVAL:
        session.last_seen_at = now
        session.expires_at = now + SESSION_LIFETIME
        db.commit()
    return user


def current_user(request: Request, db: OrmSession = Depends(get_db)) -> User:
    user = _lookup_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def current_user_optional(request: Request, db: OrmSession = Depends(get_db)) -> User | None:
    return _lookup_user(request, db)
