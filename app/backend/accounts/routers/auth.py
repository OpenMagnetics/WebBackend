"""Registration, login and account credentials.

Minimal-friction flow (per proposal v2 §4): one email field, then one password
field. /auth/check_email tells the frontend whether the password field means
"log in" or "create account". Registration is instant — no verification wall;
email verification is lazy and only gates password recovery.
"""
import datetime
import hashlib
import re
import secrets

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session as OrmSession

from .. import emailer
from ..db import get_db
from ..models import EmailToken, User
from ..ratelimit import limit
from ..security import (
    clear_session_cookie, create_session, current_user, destroy_other_sessions,
    destroy_session, hash_password, set_session_cookie, verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
VERIFY_TOKEN_LIFETIME = datetime.timedelta(days=7)
RESET_TOKEN_LIFETIME = datetime.timedelta(hours=1)


class EmailIn(BaseModel):
    email: str


class RegisterIn(BaseModel):
    email: str
    password: str
    display_name: str | None = None


class LoginIn(BaseModel):
    email: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str


def _normalize_email(email: str) -> str:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="Not a valid email address")
    return email


def _check_password_strength(password: str):
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=422, detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters")


def _user_payload(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "email_verified": user.email_verified_at is not None,
        "created_at": user.created_at.isoformat(),
    }


def _find_user(db: OrmSession, email: str) -> User | None:
    return (db.query(User)
            .filter(User.email == email, User.deleted_at.is_(None))
            .one_or_none())


def _issue_email_token(db: OrmSession, user: User, purpose: str, lifetime: datetime.timedelta) -> str:
    token = secrets.token_urlsafe(32)
    db.add(EmailToken(
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        user_id=user.id,
        purpose=purpose,
        expires_at=datetime.datetime.now(datetime.timezone.utc) + lifetime,
    ))
    db.commit()
    return token


def _consume_email_token(db: OrmSession, token: str, purpose: str) -> User:
    row = db.get(EmailToken, hashlib.sha256(token.encode()).hexdigest())
    now = datetime.datetime.now(datetime.timezone.utc)
    if row is None or row.purpose != purpose or row.used_at is not None or row.expires_at < now:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    row.used_at = now
    user = db.get(User, row.user_id)
    if user is None or user.deleted_at is not None or user.disabled_at is not None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    db.commit()
    return user


@router.post("/check_email", dependencies=[Depends(limit("check_email", 30, 60))])
def check_email(data: EmailIn, db: OrmSession = Depends(get_db)):
    email = _normalize_email(data.email)
    return {"exists": _find_user(db, email) is not None}


@router.post("/register", dependencies=[Depends(limit("register", 10, 3600))])
def register(data: RegisterIn, request: Request, response: Response,
             background_tasks: BackgroundTasks, db: OrmSession = Depends(get_db)):
    email = _normalize_email(data.email)
    _check_password_strength(data.password)
    if _find_user(db, email) is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(
        email=email,
        password_hash=hash_password(data.password),
        display_name=(data.display_name or "").strip() or email.split("@")[0],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if emailer.smtp_configured():
        token = _issue_email_token(db, user, "verify", VERIFY_TOKEN_LIFETIME)
        subject, body = emailer.verification_email(token)
        background_tasks.add_task(emailer.send_email_background, user.email, subject, body)

    set_session_cookie(response, create_session(db, user, request.headers.get("user-agent")))
    return _user_payload(user)


@router.post("/login", dependencies=[Depends(limit("login", 15, 300))])
def login(data: LoginIn, request: Request, response: Response, db: OrmSession = Depends(get_db)):
    email = _normalize_email(data.email)
    user = _find_user(db, email)
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    if user.disabled_at is not None:
        raise HTTPException(status_code=403, detail="This account is disabled")
    set_session_cookie(response, create_session(db, user, request.headers.get("user-agent")))
    return _user_payload(user)


@router.post("/logout")
def logout(request: Request, response: Response, db: OrmSession = Depends(get_db)):
    destroy_session(db, request)
    clear_session_cookie(response)
    return {"status": "logged_out"}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return _user_payload(user)


@router.post("/change_password")
def change_password(data: ChangePasswordIn, request: Request,
                    user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong current password")
    _check_password_strength(data.new_password)
    user.password_hash = hash_password(data.new_password)
    db.commit()
    destroy_other_sessions(db, user, request)
    return {"status": "password_changed"}


@router.post("/request_verify", dependencies=[Depends(limit("send_email", 5, 3600))])
def request_verify(background_tasks: BackgroundTasks,
                   user: User = Depends(current_user), db: OrmSession = Depends(get_db)):
    if user.email_verified_at is not None:
        return {"status": "already_verified"}
    if not emailer.smtp_configured():
        raise HTTPException(status_code=503, detail="Email sending is not configured on this server")
    token = _issue_email_token(db, user, "verify", VERIFY_TOKEN_LIFETIME)
    subject, body = emailer.verification_email(token)
    background_tasks.add_task(emailer.send_email_background, user.email, subject, body)
    return {"status": "verification_sent"}


class VerifyIn(BaseModel):
    token: str


@router.post("/verify_email")
def verify_email(data: VerifyIn, db: OrmSession = Depends(get_db)):
    user = _consume_email_token(db, data.token, "verify")
    user.email_verified_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    return {"status": "verified"}


@router.post("/request_password_reset", dependencies=[Depends(limit("send_email", 5, 3600))])
def request_password_reset(data: EmailIn, background_tasks: BackgroundTasks,
                           db: OrmSession = Depends(get_db)):
    if not emailer.smtp_configured():
        raise HTTPException(status_code=503, detail="Email sending is not configured on this server")
    email = _normalize_email(data.email)
    user = _find_user(db, email)
    if user is not None and user.disabled_at is None:
        token = _issue_email_token(db, user, "reset", RESET_TOKEN_LIFETIME)
        subject, body = emailer.password_reset_email(token)
        background_tasks.add_task(emailer.send_email_background, user.email, subject, body)
    # Always 200: do not reveal whether the email has an account.
    return {"status": "reset_email_sent_if_account_exists"}


@router.post("/reset_password", dependencies=[Depends(limit("reset_password", 10, 3600))])
def reset_password(data: ResetPasswordIn, db: OrmSession = Depends(get_db)):
    _check_password_strength(data.new_password)
    user = _consume_email_token(db, data.token, "reset")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"status": "password_reset"}
