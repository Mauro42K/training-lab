"""init phase3 postgres foundation

Revision ID: 20260305_01
Revises:
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260305_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("timezone", sa.String(length=64), server_default=sa.text("'America/New_York'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=100), server_default=sa.text("'default'"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_api_keys_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_api_keys"),
        sa.UniqueConstraint("key_hash", name="uq_api_keys_key_hash"),
    )

    op.create_table(
        "workouts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("healthkit_workout_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sport", sa.String(length=16), nullable=False),
        sa.Column("start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_sec", sa.Integer(), nullable=False),
        sa.Column("distance_m", sa.Float(), nullable=True),
        sa.Column("energy_kcal", sa.Float(), nullable=True),
        sa.Column("source_bundle_id", sa.String(length=255), nullable=True),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "sport IN ('run','bike','strength','walk','other')",
            name="ck_workouts_workouts_sport_allowed",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_workouts_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_workouts"),
        sa.UniqueConstraint(
            "user_id",
            "healthkit_workout_uuid",
            name="uq_workouts_user_hk_uuid",
        ),
    )
    op.create_index("ix_workouts_user_id", "workouts", ["user_id"])
    op.create_index("ix_workouts_start", "workouts", ["start"])

    op.create_table(
        "ingest_idempotency",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=128), nullable=False),
        sa.Column("response_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_ingest_idempotency_user_id_users", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ingest_idempotency"),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_ingest_idempotency_user_key"),
    )
    op.create_index("ix_ingest_idempotency_created_at", "ingest_idempotency", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ingest_idempotency_created_at", table_name="ingest_idempotency")
    op.drop_table("ingest_idempotency")
    op.drop_index("ix_workouts_start", table_name="workouts")
    op.drop_index("ix_workouts_user_id", table_name="workouts")
    op.drop_table("workouts")
    op.drop_table("api_keys")
    op.drop_table("users")
