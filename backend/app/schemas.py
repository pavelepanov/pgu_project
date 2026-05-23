from pydantic import BaseModel, Field


class MealEntryCreate(BaseModel):
    product_id: int = Field(gt=0)
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    grams: int = Field(gt=0, le=1000000)


class ManualMealEntryCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=255)
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    grams: int = Field(default=100, gt=0, le=1000000)
    calories: int = Field(ge=0, le=1000000)
    protein: float = Field(ge=0, le=10000)
    fat: float = Field(ge=0, le=10000)
    carbs: float = Field(ge=0, le=10000)


class RecognizedMealCreate(BaseModel):
    food_name: str = Field(min_length=1, max_length=255)
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    estimated_grams: int = Field(gt=0, le=1000000)
    calories_per_100g: float = Field(ge=0, le=10000)
    protein_per_100g: float = Field(ge=0, le=10000)
    fat_per_100g: float = Field(ge=0, le=10000)
    carbs_per_100g: float = Field(ge=0, le=10000)


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


class ProfileUpdate(BaseModel):
    height_cm: int | None = Field(default=None, ge=50, le=300)
    weight_kg: float | None = Field(default=None, ge=20, le=500)
    age: int | None = Field(default=None, ge=10, le=120)
    fitness_goal: str | None = Field(default=None, pattern="^(lose|gain|maintain)$")
    protein_target: int | None = Field(default=None, ge=0, le=1000)
    fat_target: int | None = Field(default=None, ge=0, le=500)
    carbs_target: int | None = Field(default=None, ge=0, le=500)


class RegisterRequest(BaseModel):
    height_cm: int = Field(ge=50, le=300)
    weight_kg: float = Field(ge=20, le=500)
    age: int = Field(ge=10, le=120)
    fitness_goal: str = Field(pattern="^(lose|gain|maintain)$")
