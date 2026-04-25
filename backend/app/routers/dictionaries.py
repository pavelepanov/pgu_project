from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_current_user
from app.db import get_db
from app.models import User

router = APIRouter(prefix="/api/dictionaries", tags=["dictionaries"])


@router.get("/foods")
def foods(
    query: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"items": crud.search_foods(db, query)}


@router.get("/exercises")
def exercises(
    query: str | None = Query(default=None, max_length=80),
    muscle_group: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"items": crud.search_exercises(db, query, muscle_group)}
