from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import ManualMealEntryCreate, MealEntryCreate, RecognizedMealCreate
from app.food_recognition import recognize_food_from_image, calculate_nutrition_values

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


@router.get("/today")
def today_nutrition(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_today_nutrition(db, current_user)


@router.post("/entries", status_code=201)
def create_entry(
    payload: MealEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.create_meal_entry(db, current_user, payload)


@router.post("/manual", status_code=201)
def create_manual_entry(
    payload: ManualMealEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.create_manual_meal_entry(db, current_user, payload)


@router.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.delete_meal_entry(db, current_user, entry_id)


@router.post("/recognize")
async def recognize_food_endpoint(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Загрузите изображение")

    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Изображение слишком большое (макс 10MB)")

    recognized = await recognize_food_from_image(image_bytes)
    if not recognized:
        return {
            "success": False,
            "message": "Не удалось распознать блюдо. Попробуйте сфотографировать при лучшем освещении или добавьте вручную.",
            "recognized": None,
        }

    nutrition = calculate_nutrition_values(recognized)
    similar_product = crud.find_similar_food(db, recognized.get("food_name", ""))

    return {
        "success": True,
        "recognized": {
            **recognized,
            "nutrition": nutrition,
        },
        "suggestion": similar_product,
        "message": f"Распознано: {recognized['food_name']} ({recognized['estimated_grams']}г)",
    }


@router.post("/entries/from-recognition", status_code=201)
def create_entry_from_recognition(
    payload: RecognizedMealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    multiplier = payload.estimated_grams / 100.0
    entry_payload = ManualMealEntryCreate(
        product_name=payload.food_name,
        meal_type=payload.meal_type,
        grams=payload.estimated_grams,
        calories=round(payload.calories_per_100g * multiplier),
        protein=round(payload.protein_per_100g * multiplier, 2),
        fat=round(payload.fat_per_100g * multiplier, 2),
        carbs=round(payload.carbs_per_100g * multiplier, 2),
    )
    return crud.create_manual_meal_entry(db, current_user, entry_payload)
