from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import TrackingUpdate
from app.crud_ext import get_today_tracking, upsert_daily_tracking
from app import crud

router = APIRouter(prefix="/api/tracking", tags=["tracking"])


@router.get("/today")
def get_tracking(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_today_tracking(db, current_user)


@router.post("/today")
def update_tracking(
    payload: TrackingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return upsert_daily_tracking(db, current_user, payload.sleep_hours, payload.water_liters)


@router.get("/summary")
async def daily_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get AI-powered daily summary with all metrics.
    Includes nutrition, workouts, tracking, and profile data.
    """
    nutrition = crud.get_today_nutrition(db, current_user)
    workouts = crud.get_today_workouts(db, current_user)
    tracking = get_today_tracking(db, current_user)
    profile = crud.get_profile(db, current_user)

    # Generate AI summary
    try:
        from app.ai_summary import generate_daily_summary
        summary_text = await generate_daily_summary(
            current_user,
            nutrition,
            workouts,
            tracking,
        )
    except Exception as e:
        summary_text = f"Ошибка при генерации сводки: {str(e)}"

    return {
        "summary": summary_text,
        "date": nutrition.get("date"),
        "nutrition": nutrition,
        "workouts": workouts,
        "tracking": tracking,
        "profile": profile,
    }
