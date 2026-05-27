from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_current_user
from app.db import get_db
from app.models import User

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/range")
def range_stats(
    date_from: date = Query(),
    date_to: date = Query(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_stats(db, current_user, date_from, date_to)


@router.get("/exercises/{exercise_id}")
def exercise_stats(
    exercise_id: int,
    date_from: date = Query(),
    date_to: date = Query(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_exercise_stats(db, current_user, exercise_id, date_from, date_to)
