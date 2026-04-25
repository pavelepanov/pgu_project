"""add workout plans

Revision ID: 0002_workout_plans
Revises: 0001_initial_schema_and_seed
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_workout_plans"
down_revision = "0001_initial_schema_and_seed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workout_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_telegram_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workout_plans_user_telegram_id", "workout_plans", ["user_telegram_id"], unique=False)

    op.create_table(
        "workout_plan_exercises",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("target_sets", sa.Integer(), server_default="3", nullable=False),
        sa.Column("target_reps", sa.Integer(), server_default="10", nullable=False),
        sa.Column("target_weight_kg", sa.Numeric(8, 2), nullable=True),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"]),
        sa.ForeignKeyConstraint(["plan_id"], ["workout_plans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workout_plan_exercises_exercise_id", "workout_plan_exercises", ["exercise_id"], unique=False)
    op.create_index("ix_workout_plan_exercises_plan_id", "workout_plan_exercises", ["plan_id"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO workout_plans (title, description, is_default)
            SELECT 'Фулбоди новичок', 'Базовая тренировка на все тело для старта.', true
            WHERE NOT EXISTS (SELECT 1 FROM workout_plans WHERE title = 'Фулбоди новичок' AND is_default = true);

            INSERT INTO workout_plans (title, description, is_default)
            SELECT 'Верх тела', 'Грудь, спина, плечи и руки.', true
            WHERE NOT EXISTS (SELECT 1 FROM workout_plans WHERE title = 'Верх тела' AND is_default = true);

            INSERT INTO workout_plans (title, description, is_default)
            SELECT 'Ноги и корпус', 'Ноги, спина и стабилизация корпуса.', true
            WHERE NOT EXISTS (SELECT 1 FROM workout_plans WHERE title = 'Ноги и корпус' AND is_default = true);
            """
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO workout_plan_exercises (plan_id, exercise_id, position, target_sets, target_reps)
            SELECT p.id, e.id, v.position, v.target_sets, v.target_reps
            FROM workout_plans p
            JOIN (
                VALUES
                    ('Фулбоди новичок', 'Присед со штангой', 1, 3, 10),
                    ('Фулбоди новичок', 'Жим лежа', 2, 3, 8),
                    ('Фулбоди новичок', 'Тяга верхнего блока', 3, 3, 10),
                    ('Фулбоди новичок', 'Планка', 4, 3, 45),
                    ('Верх тела', 'Жим лежа', 1, 4, 8),
                    ('Верх тела', 'Тяга верхнего блока', 2, 4, 10),
                    ('Верх тела', 'Жим гантелей сидя', 3, 3, 10),
                    ('Верх тела', 'Подъем штанги на бицепс', 4, 3, 12),
                    ('Ноги и корпус', 'Присед со штангой', 1, 4, 8),
                    ('Ноги и корпус', 'Становая тяга', 2, 3, 6),
                    ('Ноги и корпус', 'Велотренажер', 3, 1, 20),
                    ('Ноги и корпус', 'Планка', 4, 3, 60)
            ) AS v(plan_title, exercise_name, position, target_sets, target_reps)
              ON v.plan_title = p.title
            JOIN exercises e ON e.name = v.exercise_name
            WHERE NOT EXISTS (
                SELECT 1
                FROM workout_plan_exercises existing
                WHERE existing.plan_id = p.id AND existing.exercise_id = e.id AND existing.position = v.position
            );
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_workout_plan_exercises_plan_id", table_name="workout_plan_exercises")
    op.drop_index("ix_workout_plan_exercises_exercise_id", table_name="workout_plan_exercises")
    op.drop_table("workout_plan_exercises")
    op.drop_index("ix_workout_plans_user_telegram_id", table_name="workout_plans")
    op.drop_table("workout_plans")
