import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.refresh_token import RefreshToken


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


async def issue_refresh_token(db: AsyncSession, user_id: int) -> str:
    raw = secrets.token_urlsafe(48)
    db.add(RefreshToken(
        user_id=user_id,
        token_hash=_hash(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        ),
    ))
    await db.flush()
    return raw


async def rotate_refresh_token(
    db: AsyncSession,
    raw: str,
) -> tuple[int, str] | None:
    digest = _hash(raw)
    now = datetime.now(timezone.utc)
    replacement = secrets.token_urlsafe(48)
    replacement_hash = _hash(replacement)
    consumed = await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == digest,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .values(
            revoked_at=now,
            replaced_by_hash=replacement_hash,
        )
        .returning(RefreshToken.user_id)
    )
    user_id = consumed.scalar_one_or_none()
    if user_id is None:
        return None
    db.add(RefreshToken(
        user_id=user_id,
        token_hash=replacement_hash,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    await db.flush()
    return user_id, replacement


async def revoke_refresh_token(db: AsyncSession, raw: str | None) -> None:
    if not raw:
        return
    record = (
        await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == _hash(raw))
        )
    ).scalar_one_or_none()
    if record and record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
