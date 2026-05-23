from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import ManualMealEntryCreate, MealEntryCreate

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


@router.post("/photo")
def recognize_photo(request: Request, current_user: User = Depends(get_current_user)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Распознавание еды по фото не поддерживается в этой версии приложения.")
