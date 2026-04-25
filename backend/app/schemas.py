from pydantic import BaseModel, Field


class MealEntryCreate(BaseModel):
    product_id: int = Field(gt=0)
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    grams: int = Field(gt=0, le=100000)


class ManualMealEntryCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    grams: int = Field(default=100, gt=0, le=100000)
    calories: int = Field(ge=0, le=100000)
    protein: float = Field(ge=0, le=10000)
    fat: float = Field(ge=0, le=10000)
    carbs: float = Field(ge=0, le=10000)


class WorkoutCreate(BaseModel):
    title: str = Field(default="Тренировка", min_length=1, max_length=255)


class WorkoutSetCreate(BaseModel):
    exercise_id: int = Field(gt=0)
    weight_kg: float = Field(default=0, ge=0, le=2000)
    reps: int = Field(default=1, gt=0, le=1000)
    duration_min: float | None = Field(default=None, ge=0, le=10000)
    distance_km: float | None = Field(default=None, ge=0, le=10000)
    speed_kmh: float | None = Field(default=None, ge=0, le=300)
    pace_min_per_km: float | None = Field(default=None, ge=0, le=1000)


class WorkoutPlanExerciseCreate(BaseModel):
    exercise_id: int = Field(gt=0)
    target_sets: int = Field(default=3, ge=1, le=20)
    target_reps: int = Field(default=10, ge=1, le=300)
    target_weight_kg: float | None = Field(default=None, ge=0, le=2000)


class WorkoutPlanCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    exercises: list[WorkoutPlanExerciseCreate] = Field(min_length=1, max_length=30)
