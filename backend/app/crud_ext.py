# Дополнительные CRUD функции для сна, воды и AI-сводки
# Добавить в конец app/crud.py

from datetime import UTC, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import models
from app.xp import calculate_level


def _optional_money(value: Decimal | float | int | None) -> Decimal | None:
    """Convert value to Decimal, return None if value is None"""
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=__import__('decimal').ROUND_HALF_UP)


def upsert_daily_tracking(db: Session, user: models.User, sleep_hours: float | None = None, water_liters: float | None = None) -> dict:
    """Upsert daily tracking for sleep and water intake"""
    from datetime import date
    
    today = date.today()
    tracking = (
        db.query(models.DailyTracking)
        .filter(
            models.DailyTracking.user_telegram_id == user.telegram_id,
            models.DailyTracking.tracked_date == today,
        )
        .one_or_none()
    )

    if tracking:
        if sleep_hours is not None:
            tracking.sleep_hours = _optional_money(sleep_hours)
        if water_liters is not None:
            tracking.water_liters = _optional_money(water_liters)
    else:
        tracking = models.DailyTracking(
            user_telegram_id=user.telegram_id,
            tracked_date=today,
            sleep_hours=_optional_money(sleep_hours) if sleep_hours is not None else None,
            water_liters=_optional_money(water_liters) if water_liters is not None else None,
        )
        db.add(tracking)

    db.commit()
    db.refresh(tracking)
    return {
        "tracked_date": tracking.tracked_date.isoformat(),
        "sleep_hours": float(tracking.sleep_hours) if tracking.sleep_hours else None,
        "water_liters": float(tracking.water_liters) if tracking.water_liters else None,
    }


def get_today_tracking(db: Session, user: models.User) -> dict:
    """Get today's sleep and water tracking"""
    from datetime import date
    
    today = date.today()
    tracking = (
        db.query(models.DailyTracking)
        .filter(
            models.DailyTracking.user_telegram_id == user.telegram_id,
            models.DailyTracking.tracked_date == today,
        )
        .one_or_none()
    )

    if tracking:
        return {
            "tracked_date": tracking.tracked_date.isoformat(),
            "sleep_hours": float(tracking.sleep_hours) if tracking.sleep_hours else None,
            "water_liters": float(tracking.water_liters) if tracking.water_liters else None,
        }
    return {
        "tracked_date": today.isoformat(),
        "sleep_hours": None,
        "water_liters": None,
    }
