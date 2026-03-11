"""phase45 daily domains foundation

Revision ID: 20260311_01
Revises: 20260306_03
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260311_01"
down_revision = "20260306_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sleep_sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("healthkit_sleep_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("category_value", sa.String(length=32), nullable=True),
        sa.Column("source_bundle_id", sa.String(length=255), nullable=True),
        sa.Column("provider", sa.String(length=32), server_default=sa.text("'apple_health'"), nullable=False),
        sa.Column("source_count", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("has_mixed_sources", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("primary_device_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("end_at >= start_at", name="ck_sleep_sessions_time_range"),
        sa.CheckConstraint("provider = 'apple_health'", name="ck_sleep_sessions_provider_allowed"),
        sa.CheckConstraint("source_count >= 1", name="ck_sleep_sessions_source_count_positive"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_sleep_sessions_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_sleep_sessions"),
        sa.UniqueConstraint("user_id", "healthkit_sleep_uuid", name="uq_sleep_sessions_user_hk_uuid"),
    )
    op.create_index("ix_sleep_sessions_user_local_date", "sleep_sessions", ["user_id", "local_date"])
    op.create_index("ix_sleep_sessions_user_end_at", "sleep_sessions", ["user_id", "end_at"])

    op.create_table(
        "recovery_signals",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("healthkit_signal_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signal_type", sa.String(length=32), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("signal_value", sa.Float(), nullable=False),
        sa.Column("source_bundle_id", sa.String(length=255), nullable=True),
        sa.Column("provider", sa.String(length=32), server_default=sa.text("'apple_health'"), nullable=False),
        sa.Column("source_count", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("has_mixed_sources", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("primary_device_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("signal_type IN ('hrv_sdnn','resting_hr')", name="ck_recovery_signals_type_allowed"),
        sa.CheckConstraint("signal_value >= 0", name="ck_recovery_signals_value_non_negative"),
        sa.CheckConstraint("provider = 'apple_health'", name="ck_recovery_signals_provider_allowed"),
        sa.CheckConstraint("source_count >= 1", name="ck_recovery_signals_source_count_positive"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_recovery_signals_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_recovery_signals"),
        sa.UniqueConstraint("user_id", "healthkit_signal_uuid", name="uq_recovery_signals_user_hk_uuid"),
    )
    op.create_index("ix_recovery_signals_user_local_date", "recovery_signals", ["user_id", "local_date"])
    op.create_index("ix_recovery_signals_user_type_date", "recovery_signals", ["user_id", "signal_type", "local_date"])

    op.create_table(
        "body_measurements",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("healthkit_measurement_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("measurement_type", sa.String(length=32), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("measurement_value", sa.Float(), nullable=False),
        sa.Column("source_bundle_id", sa.String(length=255), nullable=True),
        sa.Column("provider", sa.String(length=32), server_default=sa.text("'apple_health'"), nullable=False),
        sa.Column("source_count", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("has_mixed_sources", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("primary_device_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "measurement_type IN ('weight_kg','body_fat_pct','lean_body_mass_kg')",
            name="ck_body_measurements_type_allowed",
        ),
        sa.CheckConstraint("measurement_value >= 0", name="ck_body_measurements_value_non_negative"),
        sa.CheckConstraint("provider = 'apple_health'", name="ck_body_measurements_provider_allowed"),
        sa.CheckConstraint("source_count >= 1", name="ck_body_measurements_source_count_positive"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_body_measurements_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_body_measurements"),
        sa.UniqueConstraint("user_id", "healthkit_measurement_uuid", name="uq_body_measurements_user_hk_uuid"),
    )
    op.create_index("ix_body_measurements_user_local_date", "body_measurements", ["user_id", "local_date"])
    op.create_index("ix_body_measurements_user_type_date", "body_measurements", ["user_id", "measurement_type", "local_date"])

    op.create_table(
        "daily_sleep_summary",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("total_sleep_sec", sa.Integer(), nullable=False),
        sa.Column("main_sleep_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("main_sleep_end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("main_sleep_duration_sec", sa.Integer(), nullable=False),
        sa.Column("naps_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("naps_total_sleep_sec", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("completeness_status", sa.String(length=16), nullable=False),
        sa.Column("provider", sa.String(length=32), server_default=sa.text("'apple_health'"), nullable=False),
        sa.Column("source_count", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("has_mixed_sources", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("primary_device_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("completeness_status IN ('complete','partial')", name="ck_daily_sleep_summary_completeness_allowed"),
        sa.CheckConstraint("total_sleep_sec >= 0", name="ck_daily_sleep_summary_total_non_negative"),
        sa.CheckConstraint("main_sleep_duration_sec >= 0", name="ck_daily_sleep_summary_main_duration_non_negative"),
        sa.CheckConstraint("naps_count >= 0", name="ck_daily_sleep_summary_naps_count_non_negative"),
        sa.CheckConstraint("naps_total_sleep_sec >= 0", name="ck_daily_sleep_summary_naps_total_non_negative"),
        sa.CheckConstraint("main_sleep_end_at >= main_sleep_start_at", name="ck_daily_sleep_summary_main_sleep_range"),
        sa.CheckConstraint("provider = 'apple_health'", name="ck_daily_sleep_summary_provider_allowed"),
        sa.CheckConstraint("source_count >= 1", name="ck_daily_sleep_summary_source_count_positive"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_daily_sleep_summary_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_daily_sleep_summary"),
        sa.UniqueConstraint("user_id", "local_date", name="uq_daily_sleep_summary_user_date"),
    )
    op.create_index("ix_daily_sleep_summary_user_local_date", "daily_sleep_summary", ["user_id", "local_date"])

    op.create_table(
        "daily_activity",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("steps", sa.Integer(), nullable=True),
        sa.Column("walking_running_distance_m", sa.Float(), nullable=True),
        sa.Column("active_energy_kcal", sa.Float(), nullable=True),
        sa.Column("completeness_status", sa.String(length=16), nullable=False),
        sa.Column("provider", sa.String(length=32), server_default=sa.text("'apple_health'"), nullable=False),
        sa.Column("source_count", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("has_mixed_sources", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("primary_device_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("completeness_status IN ('complete','partial')", name="ck_daily_activity_completeness_allowed"),
        sa.CheckConstraint("steps IS NULL OR steps >= 0", name="ck_daily_activity_steps_non_negative"),
        sa.CheckConstraint("walking_running_distance_m IS NULL OR walking_running_distance_m >= 0", name="ck_daily_activity_distance_non_negative"),
        sa.CheckConstraint("active_energy_kcal IS NULL OR active_energy_kcal >= 0", name="ck_daily_activity_energy_non_negative"),
        sa.CheckConstraint("(steps IS NOT NULL OR walking_running_distance_m IS NOT NULL OR active_energy_kcal IS NOT NULL)", name="ck_daily_activity_has_value"),
        sa.CheckConstraint("provider = 'apple_health'", name="ck_daily_activity_provider_allowed"),
        sa.CheckConstraint("source_count >= 1", name="ck_daily_activity_source_count_positive"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_daily_activity_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_daily_activity"),
        sa.UniqueConstraint("user_id", "local_date", name="uq_daily_activity_user_date"),
    )
    op.create_index("ix_daily_activity_user_local_date", "daily_activity", ["user_id", "local_date"])

    op.create_table(
        "daily_recovery",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("sleep_total_sec", sa.Integer(), nullable=True),
        sa.Column("hrv_sdnn_ms", sa.Float(), nullable=True),
        sa.Column("resting_hr_bpm", sa.Float(), nullable=True),
        sa.Column("activity_present", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("load_present", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("inputs_present", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("inputs_missing", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("completeness_status", sa.String(length=16), nullable=False),
        sa.Column("has_estimated_inputs", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("provider", sa.String(length=32), server_default=sa.text("'apple_health'"), nullable=False),
        sa.Column("source_count", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("has_mixed_sources", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("primary_device_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("completeness_status IN ('complete','partial')", name="ck_daily_recovery_completeness_allowed"),
        sa.CheckConstraint("sleep_total_sec IS NULL OR sleep_total_sec >= 0", name="ck_daily_recovery_sleep_total_non_negative"),
        sa.CheckConstraint("hrv_sdnn_ms IS NULL OR hrv_sdnn_ms >= 0", name="ck_daily_recovery_hrv_non_negative"),
        sa.CheckConstraint("resting_hr_bpm IS NULL OR resting_hr_bpm >= 0", name="ck_daily_recovery_rhr_non_negative"),
        sa.CheckConstraint("(sleep_total_sec IS NOT NULL OR hrv_sdnn_ms IS NOT NULL OR resting_hr_bpm IS NOT NULL)", name="ck_daily_recovery_requires_physiological_input"),
        sa.CheckConstraint("provider = 'apple_health'", name="ck_daily_recovery_provider_allowed"),
        sa.CheckConstraint("source_count >= 1", name="ck_daily_recovery_source_count_positive"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_daily_recovery_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_daily_recovery"),
        sa.UniqueConstraint("user_id", "local_date", name="uq_daily_recovery_user_date"),
    )
    op.create_index("ix_daily_recovery_user_local_date", "daily_recovery", ["user_id", "local_date"])


def downgrade() -> None:
    op.drop_index("ix_daily_recovery_user_local_date", table_name="daily_recovery")
    op.drop_table("daily_recovery")

    op.drop_index("ix_daily_activity_user_local_date", table_name="daily_activity")
    op.drop_table("daily_activity")

    op.drop_index("ix_daily_sleep_summary_user_local_date", table_name="daily_sleep_summary")
    op.drop_table("daily_sleep_summary")

    op.drop_index("ix_body_measurements_user_type_date", table_name="body_measurements")
    op.drop_index("ix_body_measurements_user_local_date", table_name="body_measurements")
    op.drop_table("body_measurements")

    op.drop_index("ix_recovery_signals_user_type_date", table_name="recovery_signals")
    op.drop_index("ix_recovery_signals_user_local_date", table_name="recovery_signals")
    op.drop_table("recovery_signals")

    op.drop_index("ix_sleep_sessions_user_end_at", table_name="sleep_sessions")
    op.drop_index("ix_sleep_sessions_user_local_date", table_name="sleep_sessions")
    op.drop_table("sleep_sessions")
