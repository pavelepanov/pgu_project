from pydantic import BaseModel, Field, ConfigDict, model_validator, validator


FOOD_GRAMS_MAX = 5000
MANUAL_CALORIES_MAX = 10000
MANUAL_PROTEIN_MAX = 500
MANUAL_FAT_MAX = 300
MANUAL_CARBS_MAX = 800


class MealEntryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(gt=0)
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    grams: int = Field(gt=0, le=FOOD_GRAMS_MAX)


class ManualMealEntryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_name: str = Field(min_length=1, max_length=255)
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    grams: int = Field(default=100, gt=0, le=FOOD_GRAMS_MAX)
    calories: int = Field(ge=0, le=MANUAL_CALORIES_MAX)
    protein: float = Field(ge=0, le=MANUAL_PROTEIN_MAX)
    fat: float = Field(ge=0, le=MANUAL_FAT_MAX)
    carbs: float = Field(ge=0, le=MANUAL_CARBS_MAX)

    @validator("product_name", pre=True, always=True)
    def strip_product_name(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_energy_balance(self):
        macro_calories = self.protein * 4 + self.fat * 9 + self.carbs * 4
        if self.calories == 0 and macro_calories > 0:
            raise ValueError("Калории не могут быть 0, если указаны БЖУ")
        if self.calories > 0 and macro_calories > self.calories * 1.35:
            raise ValueError("БЖУ дают больше калорий, чем указано в поле ккал")
        return self


class RecognizedMealCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    food_name: str = Field(min_length=1, max_length=255)
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    estimated_grams: int = Field(gt=0, le=FOOD_GRAMS_MAX)
    calories_per_100g: float = Field(ge=0, le=MANUAL_CALORIES_MAX)
    protein_per_100g: float = Field(ge=0, le=MANUAL_PROTEIN_MAX)
    fat_per_100g: float = Field(ge=0, le=MANUAL_FAT_MAX)
    carbs_per_100g: float = Field(ge=0, le=MANUAL_CARBS_MAX)

    @validator("food_name", pre=True, always=True)
    def strip_food_name(cls, value: str) -> str:
        return value.strip()


class WorkoutCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(default="Тренировка", min_length=1, max_length=255)

    @validator("title", pre=True, always=True)
    def strip_title(cls, value: str) -> str:
        return value.strip() or "Тренировка"


class WorkoutSetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exercise_id: int = Field(gt=0)
    weight_kg: float = Field(default=0, ge=0, le=2000)
    reps: int = Field(default=1, gt=0, le=1000)
    duration_min: float | None = Field(default=None, ge=0, le=10000)
    distance_km: float | None = Field(default=None, ge=0, le=10000)
    speed_kmh: float | None = Field(default=None, ge=0, le=300)
    pace_min_per_km: float | None = Field(default=None, ge=0, le=1000)

    @validator("duration_min", "distance_km", "speed_kmh", "pace_min_per_km", pre=True, always=True)
    def normalize_optional_numeric(cls, value):
        return value if value is not None else None


class WorkoutPlanExerciseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exercise_id: int = Field(gt=0)
    target_sets: int = Field(default=3, ge=1, le=20)
    target_reps: int = Field(default=10, ge=1, le=300)
    target_weight_kg: float | None = Field(default=None, ge=0, le=2000)


class WorkoutPlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    exercises: list[WorkoutPlanExerciseCreate] = Field(min_length=1, max_length=30)

    @validator("title", pre=True, always=True)
    def strip_title(cls, value: str) -> str:
        return value.strip()

    @validator("description", pre=True, always=True)
    def strip_description(cls, value):
        return value.strip() if isinstance(value, str) else value


class TrackingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    water_liters: float | None = Field(default=None, ge=0, le=100)


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    height_cm: int | None = Field(default=None, ge=50, le=300)
    weight_kg: float | None = Field(default=None, ge=20, le=500)
    age: int | None = Field(default=None, ge=10, le=120)
    fitness_goal: str | None = Field(default=None, pattern="^(lose|gain|maintain)$")
    protein_target: int | None = Field(default=None, ge=0, le=1000)
    fat_target: int | None = Field(default=None, ge=0, le=500)
    carbs_target: int | None = Field(default=None, ge=0, le=500)

    @validator("fitness_goal", pre=True, always=True)
    def normalize_goal(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    height_cm: int = Field(ge=50, le=300)
    weight_kg: float = Field(ge=20, le=500)
    age: int = Field(ge=10, le=120)
    fitness_goal: str = Field(pattern="^(lose|gain|maintain)$")

    @validator("fitness_goal", pre=True, always=True)
    def normalize_goal(cls, value):
        return value.strip().lower() if isinstance(value, str) else value
