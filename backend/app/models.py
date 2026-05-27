from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    xp_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[Numeric | None] = mapped_column(Numeric(8, 2), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fitness_goal: Mapped[str | None] = mapped_column(String(80), nullable=True, default="maintain")
    registration_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    protein_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fat_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    carbs_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    meals = relationship("MealEntry", back_populates="user", cascade="all, delete-orphan")
    workouts = relationship("Workout", back_populates="user", cascade="all, delete-orphan")
    records = relationship("PersonalRecord", back_populates="user", cascade="all, delete-orphan")
    daily_tracking = relationship("DailyTracking", back_populates="user", cascade="all, delete-orphan")


class FoodProduct(Base):
    __tablename__ = "food_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    calories_per_100g: Mapped[int] = mapped_column(Integer, nullable=False)
    protein_per_100g = mapped_column(Numeric(8, 2), nullable=False)
    fat_per_100g = mapped_column(Numeric(8, 2), nullable=False)
    carbs_per_100g = mapped_column(Numeric(8, 2), nullable=False)
    default_grams: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class MealEntry(Base):
    __tablename__ = "meal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("food_products.id"), nullable=True)
    meal_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    grams: Mapped[int] = mapped_column(Integer, nullable=False)
    calories: Mapped[int] = mapped_column(Integer, nullable=False)
    protein = mapped_column(Numeric(8, 2), nullable=False)
    fat = mapped_column(Numeric(8, 2), nullable=False)
    carbs = mapped_column(Numeric(8, 2), nullable=False)
    eaten_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="meals")
    product = relationship("FoodProduct")


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    load_type: Mapped[str] = mapped_column(String(80), nullable=False)
    muscle_group: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int | None] = mapped_column(ForeignKey("users.telegram_id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    exercises = relationship("WorkoutPlanExercise", back_populates="plan", cascade="all, delete-orphan")


class WorkoutPlanExercise(Base):
    __tablename__ = "workout_plan_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("workout_plans.id"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    target_sets: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    target_reps: Mapped[int] = mapped_column(Integer, nullable=False, default=10, server_default="10")
    target_weight_kg = mapped_column(Numeric(8, 2), nullable=True)

    plan = relationship("WorkoutPlan", back_populates="exercises")
    exercise = relationship("Exercise")


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Тренировка")
    performed_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="workouts")
    sets = relationship("WorkoutSet", back_populates="workout", cascade="all, delete-orphan")


class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True)
    set_index: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg = mapped_column(Numeric(8, 2), nullable=False, default=0, server_default="0")
    reps: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_min = mapped_column(Numeric(8, 2), nullable=True)
    distance_km = mapped_column(Numeric(8, 2), nullable=True)
    speed_kmh = mapped_column(Numeric(8, 2), nullable=True)
    pace_min_per_km = mapped_column(Numeric(8, 2), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    workout = relationship("Workout", back_populates="sets")
    exercise = relationship("Exercise")


class PersonalRecord(Base):
    __tablename__ = "personal_records"
    __table_args__ = (UniqueConstraint("user_telegram_id", "exercise_id", name="uq_personal_record_user_exercise"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True)
    max_weight_kg = mapped_column(Numeric(8, 2), nullable=False, default=0, server_default="0")
    max_reps: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="records")
    exercise = relationship("Exercise")


class XpEvent(Base):
    __tablename__ = "xp_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), index=True)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    xp_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class XpRule(Base):
    __tablename__ = "xp_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    xp_amount: Mapped[int] = mapped_column(Integer, nullable=False)


class DailyTracking(Base):
    __tablename__ = "daily_tracking"
    __table_args__ = (UniqueConstraint("user_telegram_id", "tracked_date", name="uq_daily_tracking_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), index=True)
    tracked_date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    sleep_hours: Mapped[Numeric | None] = mapped_column(Numeric(5, 2), nullable=True)
    water_liters: Mapped[Numeric | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="daily_tracking")
