from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import WorkoutCreate, WorkoutPlanCreate, WorkoutSetCreate

router = APIRouter(prefix="/api", tags=["workouts"])


@router.get("/workouts/today")
def today_workouts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_today_workouts(db, current_user)


@router.get("/workout-plans")
def workout_plans(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"items": crud.get_workout_plans(db, current_user)}


@router.post("/workout-plans", status_code=201)
def create_plan(
    payload: WorkoutPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.create_workout_plan(db, current_user, payload)


@router.post("/workout-plans/{plan_id}/start", status_code=201)
def start_plan(plan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.start_workout_plan(db, current_user, plan_id)


@router.post("/workouts", status_code=201)
def create_workout(
    payload: WorkoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.create_workout(db, current_user, payload)


@router.post("/workouts/{workout_id}/sets", status_code=201)
def add_set(
    workout_id: int,
    payload: WorkoutSetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.add_workout_set(db, current_user, workout_id, payload)


@router.delete("/workouts/sets/{set_id}")
def delete_set(
    set_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.delete_workout_set(db, current_user, set_id)


@router.get("/workouts/previous-set")
def previous_set(
    exercise_id: int = Query(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"item": crud.get_previous_set(db, current_user, exercise_id)}
