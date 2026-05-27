"""initial schema and seed data

Revision ID: 0001_initial_schema_and_seed
Revises:
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema_and_seed"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=False),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("photo_url", sa.String(length=1000), nullable=True),
        sa.Column("xp_total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=False)

    op.create_table(
        "food_products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("brand", sa.String(length=255), nullable=True),
        sa.Column("calories_per_100g", sa.Integer(), nullable=False),
        sa.Column("protein_per_100g", sa.Numeric(8, 2), nullable=False),
        sa.Column("fat_per_100g", sa.Numeric(8, 2), nullable=False),
        sa.Column("carbs_per_100g", sa.Numeric(8, 2), nullable=False),
        sa.Column("default_grams", sa.Integer(), server_default="100", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_food_products_name", "food_products", ["name"], unique=False)

    op.create_table(
        "exercises",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("load_type", sa.String(length=80), nullable=False),
        sa.Column("muscle_group", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_exercises_muscle_group", "exercises", ["muscle_group"], unique=False)
    op.create_index("ix_exercises_name", "exercises", ["name"], unique=False)

    op.create_table(
        "xp_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("xp_amount", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "meal_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("meal_type", sa.String(length=40), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("grams", sa.Integer(), nullable=False),
        sa.Column("calories", sa.Integer(), nullable=False),
        sa.Column("protein", sa.Numeric(8, 2), nullable=False),
        sa.Column("fat", sa.Numeric(8, 2), nullable=False),
        sa.Column("carbs", sa.Numeric(8, 2), nullable=False),
        sa.Column("eaten_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["food_products.id"]),
        sa.ForeignKeyConstraint(["user_telegram_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_meal_entries_eaten_at", "meal_entries", ["eaten_at"], unique=False)
    op.create_index("ix_meal_entries_meal_type", "meal_entries", ["meal_type"], unique=False)
    op.create_index("ix_meal_entries_user_telegram_id", "meal_entries", ["user_telegram_id"], unique=False)

    op.create_table(
        "workouts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_telegram_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workouts_performed_at", "workouts", ["performed_at"], unique=False)
    op.create_index("ix_workouts_user_telegram_id", "workouts", ["user_telegram_id"], unique=False)

    op.create_table(
        "personal_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("max_weight_kg", sa.Numeric(8, 2), server_default="0", nullable=False),
        sa.Column("max_reps", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"]),
        sa.ForeignKeyConstraint(["user_telegram_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_telegram_id", "exercise_id", name="uq_personal_record_user_exercise"),
    )
    op.create_index("ix_personal_records_exercise_id", "personal_records", ["exercise_id"], unique=False)
    op.create_index("ix_personal_records_user_telegram_id", "personal_records", ["user_telegram_id"], unique=False)

    op.create_table(
        "workout_sets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workout_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("set_index", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(8, 2), server_default="0", nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"]),
        sa.ForeignKeyConstraint(["workout_id"], ["workouts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workout_sets_exercise_id", "workout_sets", ["exercise_id"], unique=False)
    op.create_index("ix_workout_sets_workout_id", "workout_sets", ["workout_id"], unique=False)

    op.create_table(
        "xp_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("xp_amount", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_telegram_id"], ["users.telegram_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_xp_events_user_telegram_id", "xp_events", ["user_telegram_id"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO food_products
                (name, brand, calories_per_100g, protein_per_100g, fat_per_100g, carbs_per_100g, default_grams, is_active)
            VALUES
                ('Овсянка', NULL, 379, 13.2, 6.5, 67.7, 50, true),
                ('Куриная грудка', NULL, 165, 31.0, 3.6, 0.0, 150, true),
                ('Рис вареный', NULL, 130, 2.7, 0.3, 28.0, 150, true),
                ('Яйцо куриное', NULL, 155, 13.0, 11.0, 1.1, 100, true),
                ('Творог 5%', NULL, 121, 17.0, 5.0, 1.8, 180, true),
                ('Банан', NULL, 89, 1.1, 0.3, 23.0, 120, true),
                ('Гречка вареная', NULL, 110, 3.6, 1.1, 21.3, 150, true),
                ('Лосось', NULL, 208, 20.0, 13.0, 0.0, 120, true),
                ('Йогурт натуральный', NULL, 61, 3.5, 3.3, 4.7, 150, true),
                ('Салат овощной', NULL, 45, 1.5, 2.0, 5.5, 180, true)
            ON CONFLICT (name) DO NOTHING
            """
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO exercises (name, load_type, muscle_group, is_active)
            VALUES
                ('Жим лежа', 'силовая', 'грудь', true),
                ('Присед со штангой', 'силовая', 'ноги', true),
                ('Становая тяга', 'силовая', 'спина', true),
                ('Тяга верхнего блока', 'силовая', 'спина', true),
                ('Жим гантелей сидя', 'силовая', 'плечи', true),
                ('Подъем штанги на бицепс', 'силовая', 'руки', true),
                ('Разгибание рук на блоке', 'силовая', 'руки', true),
                ('Планка', 'статическая', 'корпус', true),
                ('Беговая дорожка', 'кардио', 'все тело', true),
                ('Велотренажер', 'кардио', 'ноги', true)
            ON CONFLICT (name) DO NOTHING
            """
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO xp_rules (code, title, xp_amount)
            VALUES
                ('meal_entry', 'Добавление приема пищи', 10),
                ('workout_set', 'Добавление тренировочного подхода', 5)
            ON CONFLICT (code) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_xp_events_user_telegram_id", table_name="xp_events")
    op.drop_table("xp_events")
    op.drop_index("ix_workout_sets_workout_id", table_name="workout_sets")
    op.drop_index("ix_workout_sets_exercise_id", table_name="workout_sets")
    op.drop_table("workout_sets")
    op.drop_index("ix_personal_records_user_telegram_id", table_name="personal_records")
    op.drop_index("ix_personal_records_exercise_id", table_name="personal_records")
    op.drop_table("personal_records")
    op.drop_index("ix_workouts_user_telegram_id", table_name="workouts")
    op.drop_index("ix_workouts_performed_at", table_name="workouts")
    op.drop_table("workouts")
    op.drop_index("ix_meal_entries_user_telegram_id", table_name="meal_entries")
    op.drop_index("ix_meal_entries_meal_type", table_name="meal_entries")
    op.drop_index("ix_meal_entries_eaten_at", table_name="meal_entries")
    op.drop_table("meal_entries")
    op.drop_table("xp_rules")
    op.drop_index("ix_exercises_name", table_name="exercises")
    op.drop_index("ix_exercises_muscle_group", table_name="exercises")
    op.drop_table("exercises")
    op.drop_index("ix_food_products_name", table_name="food_products")
    op.drop_table("food_products")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
