"""expand user profile with health metrics and goals

Revision ID: 0004_user_profile_expansion
Revises: 0003_workout_activity_metrics
Create Date: 2026-05-21
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_user_profile_expansion"
down_revision = "0003_workout_activity_metrics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user profile fields
    op.add_column("users", sa.Column("height_cm", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("weight_kg", sa.Numeric(8, 2), nullable=True))
    op.add_column("users", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("fitness_goal", sa.String(80), nullable=True, server_default="maintain"))
    op.add_column("users", sa.Column("protein_target", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("fat_target", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("carbs_target", sa.Integer(), nullable=True))

    # Add daily tracking table
    op.create_table(
        "daily_tracking",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("tracked_date", sa.Date(), nullable=False, index=True),
        sa.Column("sleep_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("water_liters", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_telegram_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_telegram_id", "tracked_date", name="uq_daily_tracking_user_date"),
    )
    op.create_index("ix_daily_tracking_user_telegram_id", "daily_tracking", ["user_telegram_id"])


def downgrade() -> None:
    op.drop_index("ix_daily_tracking_user_telegram_id", table_name="daily_tracking")
    op.drop_table("daily_tracking")
    op.drop_column("users", "carbs_target")
    op.drop_column("users", "fat_target")
    op.drop_column("users", "protein_target")
    op.drop_column("users", "fitness_goal")
    op.drop_column("users", "age")
    op.drop_column("users", "weight_kg")
    op.drop_column("users", "height_cm")
