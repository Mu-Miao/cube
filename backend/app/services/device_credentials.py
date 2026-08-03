import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.device import Device
from app.models.device_pairing_code import DevicePairingCode

HASH_PREFIX = "sha256$"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def verify_device_token(device: Device | None, token: str | None) -> bool:
    if device is None or not device.token_hash or not token:
        return False
    if device.token_expires_at and _aware(device.token_expires_at) <= _utcnow():
        return False
    stored = device.token_hash
    if stored.startswith(HASH_PREFIX):
        return hmac.compare_digest(stored.removeprefix(HASH_PREFIX), hash_secret(token))
    # Staged compatibility for devices whose existing plaintext token predates the migration.
    valid = hmac.compare_digest(stored, token)
    if valid:
        device.token_hash = f"{HASH_PREFIX}{hash_secret(token)}"
        device.token_expires_at = _utcnow() + timedelta(
            seconds=settings.DEVICE_TOKEN_EXPIRE_SECONDS
        )
    return valid


def issue_device_token(device: Device) -> str:
    token = f"dev_{secrets.token_hex(32)}"
    device.token_hash = f"{HASH_PREFIX}{hash_secret(token)}"
    device.token_expires_at = _utcnow() + timedelta(
        seconds=settings.DEVICE_TOKEN_EXPIRE_SECONDS
    )
    return token


def renew_device_token(device: Device) -> None:
    """Extend a verified token without changing the token understood by firmware."""
    device.token_expires_at = _utcnow() + timedelta(
        seconds=settings.DEVICE_TOKEN_EXPIRE_SECONDS
    )


async def create_pairing_code(
    db: AsyncSession,
    device_id: str,
    created_by: int,
) -> tuple[str, DevicePairingCode]:
    raw_code = secrets.token_urlsafe(24)
    now = _utcnow()
    await db.execute(
        update(DevicePairingCode)
        .where(
            DevicePairingCode.device_id == device_id,
            DevicePairingCode.used_at.is_(None),
        )
        .values(used_at=now)
    )
    record = DevicePairingCode(
        device_id=device_id,
        code_hash=hash_secret(raw_code),
        expires_at=now + timedelta(
            minutes=settings.DEVICE_PAIRING_CODE_EXPIRE_MINUTES
        ),
        created_by=created_by,
    )
    db.add(record)
    await db.flush()
    return raw_code, record


async def consume_pairing_code(
    db: AsyncSession,
    device_id: str,
    raw_code: str | None,
) -> bool:
    if not raw_code:
        return False
    now = _utcnow()
    result = await db.execute(
        update(DevicePairingCode)
        .where(
            DevicePairingCode.device_id == device_id,
            DevicePairingCode.code_hash == hash_secret(raw_code),
            DevicePairingCode.used_at.is_(None),
            DevicePairingCode.expires_at > now,
        )
        .values(used_at=now)
        .returning(DevicePairingCode.id)
    )
    return result.scalar_one_or_none() is not None


async def authorize_handshake(
    db: AsyncSession,
    device: Device | None,
    device_id: str,
    pairing_code: str | None,
    current_token: str | None,
) -> bool:
    if await consume_pairing_code(db, device_id, pairing_code):
        return True
    if verify_device_token(device, current_token):
        return True
    return settings.DEBUG and settings.ALLOW_LEGACY_DEVICE_HANDSHAKE
