from pydantic import BaseModel, Field


class MealEntryCreate(BaseModel):
    product_id: int = Field(gt=0)
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    grams: int = Field(gt=0, le=3000)


class WorkoutCreate(BaseModel):
    title: str = Field(default="Тренировка", min_length=1, max_length=255)


class WorkoutSetCreate(BaseModel):
    exercise_id: int = Field(gt=0)
    weight_kg: float = Field(ge=0, le=500)
    reps: int = Field(gt=0, le=300)
