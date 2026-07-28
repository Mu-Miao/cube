"""create the immutable legacy Cube schema

Revision ID: 20260728_0001
Revises:
"""

from alembic import op
import sqlalchemy as sa


revision = "20260728_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("email", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("role", sa.String(20), server_default="user", nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "devices",
        sa.Column("device_id", sa.String(64), nullable=False),
        sa.Column("device_name", sa.String(100), nullable=False),
        sa.Column("token", sa.String(128), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("chip_model", sa.String(50), nullable=True),
        sa.Column("firmware_version", sa.String(20), nullable=True),
        sa.Column("bound_user_id", sa.Integer(), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["bound_user_id"], ["users.id"]),
    )
    op.create_index("ix_devices_device_id", "devices", ["device_id"], unique=True)

    op.create_table(
        "sensor_data",
        sa.Column("device_id", sa.String(64), nullable=False),
        sa.Column("temperature", sa.Double(), nullable=True),
        sa.Column("humidity", sa.Double(), nullable=True),
        sa.Column("illuminance", sa.Double(), nullable=True),
        sa.Column("aqi", sa.Double(), nullable=True),
        sa.Column("pm25", sa.Double(), nullable=True),
        sa.Column("tvoc", sa.Double(), nullable=True),
        sa.Column("eco2", sa.Double(), nullable=True),
        sa.Column("mold_risk", sa.Double(), nullable=True),
        sa.Column("gas", sa.Double(), nullable=True),
        sa.Column("wifi_rssi", sa.Integer(), nullable=True),
        sa.Column("focus_mode", sa.Integer(), nullable=True),
        sa.Column("light", sa.Integer(), nullable=True),
        sa.Column("light_brightness", sa.Integer(), nullable=True),
        sa.Column("color_temperature", sa.Integer(), nullable=True),
        sa.Column("wechat_notify", sa.Integer(), nullable=True),
        sa.Column("auto_screen_brightness", sa.Integer(), nullable=True),
        sa.Column("screen_brightness", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sensor_data_device_id", "sensor_data", ["device_id"])
    op.create_index(
        "ix_sensor_data_device_time",
        "sensor_data",
        ["device_id", "timestamp"],
    )

    op.create_table(
        "operation_logs",
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("device_id", sa.String(64), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_operation_logs_user_id", "operation_logs", ["user_id"])
    op.create_index("ix_operation_logs_device_id", "operation_logs", ["device_id"])
    op.create_index("ix_operation_logs_action", "operation_logs", ["action"])

    op.create_table(
        "voice_logs",
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("device_id", sa.String(64), nullable=True),
        sa.Column("command_text", sa.String(200), nullable=True),
        sa.Column("intent", sa.String(50), nullable=True),
        sa.Column("executed", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("response_text", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_voice_logs_user_id", "voice_logs", ["user_id"])
    op.create_index("ix_voice_logs_device_id", "voice_logs", ["device_id"])

    op.create_table(
        "ota_logs",
        sa.Column("device_id", sa.String(64), nullable=False),
        sa.Column("target_version", sa.String(32), nullable=False),
        sa.Column("firmware_url", sa.Text(), nullable=False),
        sa.Column("firmware_md5", sa.String(32), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("pushed_by", sa.Integer(), nullable=False),
        sa.Column("remark", sa.Text(), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ota_logs_device_id", "ota_logs", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_ota_logs_device_id", table_name="ota_logs")
    op.drop_table("ota_logs")
    op.drop_index("ix_voice_logs_device_id", table_name="voice_logs")
    op.drop_index("ix_voice_logs_user_id", table_name="voice_logs")
    op.drop_table("voice_logs")
    op.drop_index("ix_operation_logs_action", table_name="operation_logs")
    op.drop_index("ix_operation_logs_device_id", table_name="operation_logs")
    op.drop_index("ix_operation_logs_user_id", table_name="operation_logs")
    op.drop_table("operation_logs")
    op.drop_index("ix_sensor_data_device_time", table_name="sensor_data")
    op.drop_index("ix_sensor_data_device_id", table_name="sensor_data")
    op.drop_table("sensor_data")
    op.drop_index("ix_devices_device_id", table_name="devices")
    op.drop_table("devices")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
