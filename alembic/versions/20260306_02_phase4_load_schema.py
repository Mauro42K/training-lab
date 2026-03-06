"""phase4 load schema

Revision ID: 20260306_02
Revises: 20260305_01
Create Date: 2026-03-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260306_02"
down_revision = "20260305_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workouts", sa.Column("avg_hr_bpm", sa.Float(), nullable=True))
    op.add_column(
        "workouts",
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_check_constraint(
        "ck_workouts_avg_hr_bpm_range",
        "workouts",
        "avg_hr_bpm IS NULL OR (avg_hr_bpm >= 20 AND avg_hr_bpm <= 260)",
    )
    op.create_index("ix_workouts_is_deleted", "workouts", ["is_deleted"])

    op.create_table(
        "workout_load",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workout_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("sport", sa.String(length=16), nullable=False),
        sa.Column("trimp_value", sa.Float(), nullable=False),
        sa.Column("trimp_source", sa.String(length=16), nullable=False),
        sa.Column("trimp_model_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("trimp_method", sa.String(length=64), nullable=False),
        sa.Column("hr_rest_bpm_used", sa.Integer(), nullable=True),
        sa.Column("hr_max_bpm_used", sa.Integer(), nullable=True),
        sa.Column("intensity_factor_used", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("sport IN ('run','bike','strength','walk','other')", name="ck_workout_load_sport_allowed"),
        sa.CheckConstraint("trimp_source IN ('real','estimated')", name="ck_workout_load_trimp_source_allowed"),
        sa.CheckConstraint("trimp_value >= 0", name="ck_workout_load_trimp_non_negative"),
        sa.ForeignKeyConstraint(
            ["workout_id"],
            ["workouts.id"],
            name="fk_workout_load_workout_id_workouts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_workout_load_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_workout_load"),
        sa.UniqueConstraint(
            "workout_id",
            "trimp_model_version",
            name="uq_workout_load_workout_model_version",
        ),
    )
    op.create_index("ix_workout_load_user_local_date", "workout_load", ["user_id", "local_date"])
    op.create_index(
        "ix_workout_load_user_sport_local_date",
        "workout_load",
        ["user_id", "sport", "local_date"],
    )
    op.create_index("ix_workout_load_workout_id", "workout_load", ["workout_id"])

    op.create_table(
        "daily_load",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("sport_filter", sa.String(length=16), nullable=False),
        sa.Column("trimp_total", sa.Float(), nullable=False),
        sa.Column("sessions_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("trimp_model_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "sport_filter IN ('all','run','bike','strength','walk')",
            name="ck_daily_load_sport_filter_allowed",
        ),
        sa.CheckConstraint("trimp_total >= 0", name="ck_daily_load_trimp_non_negative"),
        sa.CheckConstraint("sessions_count >= 0", name="ck_daily_load_sessions_non_negative"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_daily_load_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_daily_load"),
        sa.UniqueConstraint(
            "user_id",
            "date",
            "sport_filter",
            "trimp_model_version",
            name="uq_daily_load_user_date_filter_model",
        ),
    )
    op.create_index("ix_daily_load_user_date", "daily_load", ["user_id", "date"])
    op.create_index("ix_daily_load_user_sport_date", "daily_load", ["user_id", "sport_filter", "date"])


def downgrade() -> None:
    op.drop_index("ix_daily_load_user_sport_date", table_name="daily_load")
    op.drop_index("ix_daily_load_user_date", table_name="daily_load")
    op.drop_table("daily_load")

    op.drop_index("ix_workout_load_workout_id", table_name="workout_load")
    op.drop_index("ix_workout_load_user_sport_local_date", table_name="workout_load")
    op.drop_index("ix_workout_load_user_local_date", table_name="workout_load")
    op.drop_table("workout_load")

    op.drop_index("ix_workouts_is_deleted", table_name="workouts")
    op.drop_constraint("ck_workouts_avg_hr_bpm_range", "workouts", type_="check")
    op.drop_column("workouts", "is_deleted")
    op.drop_column("workouts", "avg_hr_bpm")
