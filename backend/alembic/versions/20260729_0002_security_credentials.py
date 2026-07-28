"""add device credentials and refresh-token security

Revision ID: 20260729_0002
Revises: 20260728_0001
"""

import hashlib
from datetime import datetime, timedelta, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260729_0002"
down_revision = "20260728_0001"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    device_columns = {column["name"] for column in inspector.get_columns("devices")}
    if "token_expires_at" not in device_columns:
        op.add_column(
            "devices",
            sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        )

    devices = sa.table(
        "devices",
        sa.column("id", sa.Integer()),
        sa.column("token", sa.String()),
        sa.column("token_expires_at", sa.DateTime()),
    )
    expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    for row in bind.execute(
        sa.select(devices.c.id, devices.c.token, devices.c.token_expires_at)
    ):
        if not row.token:
            continue
        stored_token = row.token
        if not stored_token.startswith("sha256$"):
            digest = hashlib.sha256(stored_token.encode("utf-8")).hexdigest()
            stored_token = f"sha256${digest}"
        bind.execute(
            devices.update()
            .where(devices.c.id == row.id)
            .values(
                token=stored_token,
                token_expires_at=row.token_expires_at or expires_at,
            )
        )

    tables = _tables()
    if "device_pairing_codes" not in tables:
        op.create_table(
            "device_pairing_codes",
            sa.Column("device_id", sa.String(64), nullable=False),
            sa.Column("code_hash", sa.String(64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.UniqueConstraint("code_hash"),
        )
        op.create_index(
            "ix_device_pairing_codes_device_id",
            "device_pairing_codes",
            ["device_id"],
        )

    if "refresh_tokens" not in tables:
        op.create_table(
            "refresh_tokens",
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.Column("replaced_by_hash", sa.String(64), nullable=True),
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.UniqueConstraint("token_hash"),
        )
        op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    inspector = inspect(bind)
    sensor_indexes = {index["name"] for index in inspector.get_indexes("sensor_data")}
    if "ix_sensor_data_timestamp" not in sensor_indexes:
        op.create_index("ix_sensor_data_timestamp", "sensor_data", ["timestamp"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    sensor_indexes = {index["name"] for index in inspector.get_indexes("sensor_data")}
    if "ix_sensor_data_timestamp" in sensor_indexes:
        op.drop_index("ix_sensor_data_timestamp", table_name="sensor_data")

    tables = _tables()
    if "refresh_tokens" in tables:
        op.drop_table("refresh_tokens")
    if "device_pairing_codes" in tables:
        op.drop_table("device_pairing_codes")

    inspector = inspect(bind)
    device_columns = {column["name"] for column in inspector.get_columns("devices")}
    if "token_expires_at" in device_columns:
        with op.batch_alter_table("devices") as batch:
            batch.drop_column("token_expires_at")
