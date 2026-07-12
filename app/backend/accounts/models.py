"""Declarative models for the `accounts` schema (proposal v2, approved 2026-07-12).

Two account types: individual `users` and company `organizations` — every owned
resource has exactly one of (owner_user_id, owner_org_id), enforced by CHECK
constraints. MAS documents (designs, private parts) are stored verbatim in JSONB
columns; all ownership/versioning metadata lives in envelope columns, never
inside the MAS object (the MAS root schema is closed).

Phase 1 exposes users/sessions/email_tokens/designs/design_revisions/
user_settings through the API; the remaining tables are created now so later
phases are additive migrations only.
"""
import datetime

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index,
    Integer, Numeric, Text, text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()
SCHEMA = "accounts"


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("users_email_lower", text("lower(email)"), unique=True),
        {"schema": SCHEMA},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    email = Column(Text, nullable=False)
    email_verified_at = Column(DateTime(timezone=True))
    password_hash = Column(Text, nullable=False)
    display_name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    disabled_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))


class AuthSession(Base):
    __tablename__ = "sessions"
    __table_args__ = ({"schema": SCHEMA},)

    token_hash = Column(Text, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True))
    user_agent = Column(Text)


class EmailToken(Base):
    __tablename__ = "email_tokens"
    __table_args__ = (
        CheckConstraint("purpose IN ('verify','reset')", name="email_tokens_purpose"),
        {"schema": SCHEMA},
    )

    token_hash = Column(Text, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), nullable=False, index=True)
    purpose = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = ({"schema": SCHEMA},)

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    slug = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    deleted_at = Column(DateTime(timezone=True))


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint("role IN ('owner','admin','librarian','member','viewer')", name="memberships_role"),
        Index("memberships_org_user", "org_id", "user_id", unique=True),
        {"schema": SCHEMA},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    org_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"))  # NULL while pending
    invited_email = Column(Text)
    role = Column(Text, nullable=False)
    invited_by = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    accepted_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))


class Design(Base):
    __tablename__ = "designs"
    __table_args__ = (
        CheckConstraint("(owner_user_id IS NULL) <> (owner_org_id IS NULL)", name="designs_one_owner"),
        Index("designs_owner_user", "owner_user_id"),
        Index("designs_owner_org", "owner_org_id"),
        {"schema": SCHEMA},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"))
    owner_org_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id", ondelete="CASCADE"))
    name = Column(Text, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="SET NULL"))
    version = Column(Integer, nullable=False, server_default=text("1"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    deleted_at = Column(DateTime(timezone=True))


class DesignRevision(Base):
    __tablename__ = "design_revisions"
    __table_args__ = ({"schema": SCHEMA},)

    design_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.designs.id", ondelete="CASCADE"), primary_key=True)
    revision = Column(Integer, primary_key=True)
    mas = Column(JSONB, nullable=False)              # the MAS document, untouched
    mas_hash = Column(Text, nullable=False)          # sha256 of canonical JSON (dedup no-op saves)
    mas_version = Column(Text, nullable=False)       # MAS spec version validated against
    engine_version = Column(Text)
    schema_valid = Column(Boolean, nullable=False)
    saved_by = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="SET NULL"))
    saved_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class InventoryPart(Base):
    __tablename__ = "inventory_parts"
    __table_args__ = (
        CheckConstraint("(owner_user_id IS NULL) <> (owner_org_id IS NULL)", name="inventory_one_owner"),
        CheckConstraint("part_type IN ('coreShape','coreMaterial','core','bobbin','wire')", name="inventory_part_type"),
        CheckConstraint("source IN ('catalog','private')", name="inventory_source"),
        CheckConstraint("lifecycle IN ('draft','approved','deprecated','obsolete')", name="inventory_lifecycle"),
        Index("inv_user_name", "owner_user_id", "part_type", "name", unique=True,
              postgresql_where=text("owner_user_id IS NOT NULL AND deleted_at IS NULL")),
        Index("inv_org_name", "owner_org_id", "part_type", "name", unique=True,
              postgresql_where=text("owner_org_id IS NOT NULL AND deleted_at IS NULL")),
        {"schema": SCHEMA},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"))
    owner_org_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id", ondelete="CASCADE"))
    part_type = Column(Text, nullable=False)
    name = Column(Text, nullable=False)              # MAS name (WASM upsert key)
    source = Column(Text, nullable=False)
    catalog_ref = Column(Text)                       # public part name when source='catalog'
    mas = Column(JSONB)                              # full MAS record when source='private'
    mas_version = Column(Text)
    lifecycle = Column(Text, nullable=False, server_default=text("'approved'"))
    stock_qty = Column(Numeric)
    order_code = Column(Text)
    notes = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    deleted_at = Column(DateTime(timezone=True))


class ShareLink(Base):
    __tablename__ = "share_links"
    __table_args__ = (
        CheckConstraint("kind IN ('design','inventory')", name="share_links_kind"),
        CheckConstraint(
            "(kind = 'design' AND design_id IS NOT NULL)"
            " OR (kind = 'inventory' AND ((owner_user_id IS NULL) <> (owner_org_id IS NULL)))",
            name="share_links_target"),
        {"schema": SCHEMA},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    token = Column(Text, nullable=False, unique=True)
    kind = Column(Text, nullable=False)
    design_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.designs.id", ondelete="CASCADE"))
    pinned_revision = Column(Integer)                # NULL = latest
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"))
    owner_org_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id", ondelete="CASCADE"))
    created_by = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    revoked_at = Column(DateTime(timezone=True))
    visit_count = Column(BigInteger, nullable=False, server_default=text("0"))


class InventoryMount(Base):
    __tablename__ = "inventory_mounts"
    __table_args__ = (
        CheckConstraint("(mounter_user_id IS NULL) <> (mounter_org_id IS NULL)", name="mounts_one_owner"),
        {"schema": SCHEMA},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    share_link_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.share_links.id", ondelete="CASCADE"), nullable=False)
    mounter_user_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"))
    mounter_org_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.organizations.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    removed_at = Column(DateTime(timezone=True))


class UserSettings(Base):
    __tablename__ = "user_settings"
    __table_args__ = ({"schema": SCHEMA},)

    user_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), primary_key=True)
    settings = Column(JSONB, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = ({"schema": SCHEMA},)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    actor_id = Column(UUID(as_uuid=True))
    org_id = Column(UUID(as_uuid=True))
    action = Column(Text, nullable=False)            # 'design.save', 'member.invite', 'share.create', ...
    target = Column(Text)
    at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    detail = Column(JSONB)
