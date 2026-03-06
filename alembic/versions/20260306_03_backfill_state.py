"""phase4 backfill job state

Revision ID: 20260306_03
Revises: 20260306_02
Create Date: 2026-03-06
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260306_03"
down_revision = "20260306_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backfill_job_state",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_name", sa.String(length=100), nullable=False),
        sa.Column("trimp_model_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("status", sa.String(length=16), server_default=sa.text("'idle'"), nullable=False),
        sa.Column("last_cursor_id", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("workouts_scanned", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("workouts_persisted", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "workouts_excluded_or_deleted",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("affected_dates_rebuilt", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("batches_completed", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("last_cursor_id >= 0", name="ck_backfill_job_state_cursor_non_negative"),
        sa.CheckConstraint("workouts_scanned >= 0", name="ck_backfill_job_state_scanned_non_negative"),
        sa.CheckConstraint("workouts_persisted >= 0", name="ck_backfill_job_state_persisted_non_negative"),
        sa.CheckConstraint(
            "workouts_excluded_or_deleted >= 0",
            name="ck_backfill_job_state_excluded_non_negative",
        ),
        sa.CheckConstraint(
            "affected_dates_rebuilt >= 0",
            name="ck_backfill_job_state_dates_rebuilt_non_negative",
        ),
        sa.CheckConstraint("batches_completed >= 0", name="ck_backfill_job_state_batches_non_negative"),
        sa.CheckConstraint(
            "status IN ('idle','running','completed','failed')",
            name="ck_backfill_job_state_status_allowed",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_backfill_job_state"),
        sa.UniqueConstraint(
            "job_name",
            "trimp_model_version",
            name="uq_backfill_job_state_job_name_model_version",
        ),
    )
    op.create_index(
        "ix_backfill_job_state_status",
        "backfill_job_state",
        ["status"],
    )
    op.create_index(
        "ix_backfill_job_state_model_cursor",
        "backfill_job_state",
        ["trimp_model_version", "last_cursor_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_backfill_job_state_model_cursor", table_name="backfill_job_state")
    op.drop_index("ix_backfill_job_state_status", table_name="backfill_job_state")
    op.drop_table("backfill_job_state")
