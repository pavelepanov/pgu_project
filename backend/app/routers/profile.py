from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud
from app.ai_summary_v2 import generate_daily_summary, generate_period_summary
from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import ProfileUpdate, RegisterRequest

router = APIRouter(prefix="/api", tags=["profile"])


@router.get("/profile")
def read_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_profile(db, current_user)


@router.post("/auth/register")
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.complete_registration(db, current_user, payload)


@router.patch("/profile")
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.update_profile(db, current_user, payload)


@router.delete("/profile")
def delete_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.delete_user_account(db, current_user)


@router.post("/summary/today")
async def get_daily_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = crud.get_profile(db, current_user)
    nutrition = crud.get_today_nutrition(db, current_user)
    workouts = crud.get_today_workouts(db, current_user)
    tracking = crud.get_today_tracking(db, current_user)

    summary = await generate_daily_summary(nutrition, workouts, tracking, profile)
    return {"summary": summary}


@router.post("/summary/period")
async def get_period_summary(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import date, timedelta

    profile = crud.get_profile(db, current_user)
    date_from = date.today() - timedelta(days=days)
    date_to = date.today()

    nutrition_list = []
    workouts_list = []
    tracking_list = []

    current_date = date_from
    while current_date <= date_to:
        nutrition_list.append(crud.get_date_nutrition(db, current_user, current_date))
        workouts_list.append(crud.get_date_workouts(db, current_user, current_date))
        tracking_list.append(crud.get_date_tracking(db, current_user, current_date))
        current_date += timedelta(days=1)

    summary = await generate_period_summary(nutrition_list, workouts_list, tracking_list, profile, days)
    return {"summary": summary}
