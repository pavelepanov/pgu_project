"""add workout activity metrics

Revision ID: 0003_workout_activity_metrics
Revises: 0002_workout_plans
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_workout_activity_metrics"
down_revision = "0002_workout_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workout_sets", sa.Column("duration_min", sa.Numeric(8, 2), nullable=True))
    op.add_column("workout_sets", sa.Column("distance_km", sa.Numeric(8, 2), nullable=True))
    op.add_column("workout_sets", sa.Column("speed_kmh", sa.Numeric(8, 2), nullable=True))
    op.add_column("workout_sets", sa.Column("pace_min_per_km", sa.Numeric(8, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("workout_sets", "pace_min_per_km")
    op.drop_column("workout_sets", "speed_kmh")
    op.drop_column("workout_sets", "distance_km")
    op.drop_column("workout_sets", "duration_min")
