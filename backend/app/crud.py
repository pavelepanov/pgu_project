from datetime import UTC, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app import models
from app.xp import calculate_level, xp_for_meal_entry, xp_for_workout_set


def _today_bounds() -> tuple[datetime, datetime]:
    today = datetime.now(UTC).date()
    start = datetime.combine(today, time.min, tzinfo=UTC)
    return start, start + timedelta(days=1)


def _money(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _macro(value_per_100g, grams: int) -> Decimal:
    return _money(Decimal(value_per_100g) * Decimal(grams) / Decimal(100))


def upsert_user_from_telegram(db: Session, telegram_user: dict) -> models.User:
    user = db.get(models.User, int(telegram_user["id"]))
    if not user:
        user = models.User(telegram_id=int(telegram_user["id"]), first_name=telegram_user.get("first_name") or "User")
        db.add(user)

    user.first_name = telegram_user.get("first_name") or "User"
    user.last_name = telegram_user.get("last_name") or None
    user.username = telegram_user.get("username") or None
    user.photo_url = telegram_user.get("photo_url") or None
    db.commit()
    db.refresh(user)
    return user


def serialize_food(product: models.FoodProduct) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "brand": product.brand,
        "calories_per_100g": product.calories_per_100g,
        "protein_per_100g": float(product.protein_per_100g),
        "fat_per_100g": float(product.fat_per_100g),
        "carbs_per_100g": float(product.carbs_per_100g),
        "default_grams": product.default_grams,
    }


def serialize_exercise(exercise: models.Exercise) -> dict:
    return {
        "id": exercise.id,
        "name": exercise.name,
        "load_type": exercise.load_type,
        "muscle_group": exercise.muscle_group,
    }


def serialize_meal(entry: models.MealEntry) -> dict:
    return {
        "id": entry.id,
        "meal_type": entry.meal_type,
        "product_id": entry.product_id,
        "product_name": entry.product_name,
        "grams": entry.grams,
        "calories": entry.calories,
        "protein": float(entry.protein),
        "fat": float(entry.fat),
        "carbs": float(entry.carbs),
        "eaten_at": entry.eaten_at.isoformat() if entry.eaten_at else None,
    }


def serialize_set(workout_set: models.WorkoutSet) -> dict:
    return {
        "id": workout_set.id,
        "workout_id": workout_set.workout_id,
        "exercise_id": workout_set.exercise_id,
        "exercise_name": workout_set.exercise.name if workout_set.exercise else "",
        "set_index": workout_set.set_index,
        "weight_kg": float(workout_set.weight_kg),
        "reps": workout_set.reps,
        "created_at": workout_set.created_at.isoformat() if workout_set.created_at else None,
    }


def serialize_workout(workout: models.Workout) -> dict:
    return {
        "id": workout.id,
        "title": workout.title,
        "performed_at": workout.performed_at.isoformat() if workout.performed_at else None,
        "sets": [serialize_set(workout_set) for workout_set in sorted(workout.sets, key=lambda item: item.set_index)],
    }


def search_foods(db: Session, query: str | None) -> list[dict]:
    db_query = db.query(models.FoodProduct).filter(models.FoodProduct.is_active.is_(True))
    if query:
        db_query = db_query.filter(models.FoodProduct.name.ilike(f"%{query.strip()}%"))
    return [serialize_food(product) for product in db_query.order_by(models.FoodProduct.name).limit(30).all()]


def search_exercises(db: Session, query: str | None, muscle_group: str | None) -> list[dict]:
    db_query = db.query(models.Exercise).filter(models.Exercise.is_active.is_(True))
    if query:
        term = f"%{query.strip()}%"
        db_query = db_query.filter(or_(models.Exercise.name.ilike(term), models.Exercise.muscle_group.ilike(term)))
    if muscle_group:
        db_query = db_query.filter(models.Exercise.muscle_group.ilike(f"%{muscle_group.strip()}%"))
    return [serialize_exercise(exercise) for exercise in db_query.order_by(models.Exercise.name).limit(30).all()]


def _add_xp(db: Session, user: models.User, source_type: str, source_id: int, amount: int) -> None:
    user.xp_total = (user.xp_total or 0) + amount
    db.add(
        models.XpEvent(
            user_telegram_id=user.telegram_id,
            source_type=source_type,
            source_id=source_id,
            xp_amount=amount,
        )
    )


def create_meal_entry(db: Session, user: models.User, payload) -> dict:
    product = db.get(models.FoodProduct, payload.product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    grams = payload.grams
    calories = int((Decimal(product.calories_per_100g) * Decimal(grams) / Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    entry = models.MealEntry(
        user_telegram_id=user.telegram_id,
        product_id=product.id,
        meal_type=payload.meal_type,
        product_name=product.name,
        grams=grams,
        calories=calories,
        protein=_macro(product.protein_per_100g, grams),
        fat=_macro(product.fat_per_100g, grams),
        carbs=_macro(product.carbs_per_100g, grams),
    )
    db.add(entry)
    db.flush()
    _add_xp(db, user, "meal_entry", entry.id, xp_for_meal_entry())
    db.commit()
    db.refresh(entry)
    db.refresh(user)
    return {"entry": serialize_meal(entry), "profile": get_profile(db, user)}


def delete_meal_entry(db: Session, user: models.User, entry_id: int) -> dict:
    entry = (
        db.query(models.MealEntry)
        .filter(models.MealEntry.id == entry_id, models.MealEntry.user_telegram_id == user.telegram_id)
        .one_or_none()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal entry not found")
    db.delete(entry)
    db.commit()
    return get_today_nutrition(db, user)


def get_today_nutrition(db: Session, user: models.User) -> dict:
    start, end = _today_bounds()
    entries = (
        db.query(models.MealEntry)
        .filter(
            models.MealEntry.user_telegram_id == user.telegram_id,
            models.MealEntry.eaten_at >= start,
            models.MealEntry.eaten_at < end,
        )
        .order_by(models.MealEntry.eaten_at.desc(), models.MealEntry.id.desc())
        .all()
    )
    return {
        "date": start.date().isoformat(),
        "totals": {
            "calories": sum(entry.calories for entry in entries),
            "protein": round(sum(float(entry.protein) for entry in entries), 1),
            "fat": round(sum(float(entry.fat) for entry in entries), 1),
            "carbs": round(sum(float(entry.carbs) for entry in entries), 1),
        },
        "entries": [serialize_meal(entry) for entry in entries],
    }


def create_workout(db: Session, user: models.User, payload) -> dict:
    workout = models.Workout(user_telegram_id=user.telegram_id, title=payload.title.strip() or "Тренировка")
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return serialize_workout(workout)


def get_today_workouts(db: Session, user: models.User) -> dict:
    start, end = _today_bounds()
    workouts = (
        db.query(models.Workout)
        .filter(
            models.Workout.user_telegram_id == user.telegram_id,
            models.Workout.performed_at >= start,
            models.Workout.performed_at < end,
        )
        .order_by(models.Workout.performed_at.desc(), models.Workout.id.desc())
        .all()
    )
    total_sets = sum(len(workout.sets) for workout in workouts)
    return {"date": start.date().isoformat(), "total_sets": total_sets, "workouts": [serialize_workout(item) for item in workouts]}


def _update_personal_record(db: Session, user: models.User, workout_set: models.WorkoutSet) -> None:
    record = (
        db.query(models.PersonalRecord)
        .filter(
            models.PersonalRecord.user_telegram_id == user.telegram_id,
            models.PersonalRecord.exercise_id == workout_set.exercise_id,
        )
        .one_or_none()
    )
    if not record:
        db.add(
            models.PersonalRecord(
                user_telegram_id=user.telegram_id,
                exercise_id=workout_set.exercise_id,
                max_weight_kg=workout_set.weight_kg,
                max_reps=workout_set.reps,
            )
        )
        return

    record.max_weight_kg = max(Decimal(record.max_weight_kg), Decimal(workout_set.weight_kg))
    record.max_reps = max(record.max_reps, workout_set.reps)


def add_workout_set(db: Session, user: models.User, workout_id: int, payload) -> dict:
    workout = (
        db.query(models.Workout)
        .filter(models.Workout.id == workout_id, models.Workout.user_telegram_id == user.telegram_id)
        .one_or_none()
    )
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")

    exercise = db.get(models.Exercise, payload.exercise_id)
    if not exercise or not exercise.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    next_index = (
        db.query(func.max(models.WorkoutSet.set_index))
        .filter(models.WorkoutSet.workout_id == workout.id)
        .scalar()
        or 0
    ) + 1
    workout_set = models.WorkoutSet(
        workout_id=workout.id,
        exercise_id=exercise.id,
        set_index=next_index,
        weight_kg=_money(payload.weight_kg),
        reps=payload.reps,
    )
    db.add(workout_set)
    db.flush()
    _update_personal_record(db, user, workout_set)
    _add_xp(db, user, "workout_set", workout_set.id, xp_for_workout_set())
    db.commit()
    db.refresh(workout)
    db.refresh(user)
    return {"workout": serialize_workout(workout), "profile": get_profile(db, user)}


def get_previous_set(db: Session, user: models.User, exercise_id: int) -> dict | None:
    start, _ = _today_bounds()
    workout_set = (
        db.query(models.WorkoutSet)
        .join(models.Workout)
        .filter(
            models.Workout.user_telegram_id == user.telegram_id,
            models.WorkoutSet.exercise_id == exercise_id,
            models.Workout.performed_at < start,
        )
        .order_by(desc(models.Workout.performed_at), desc(models.WorkoutSet.id))
        .first()
    )
    return serialize_set(workout_set) if workout_set else None


def get_profile(db: Session, user: models.User) -> dict:
    level_data = calculate_level(user.xp_total or 0)
    records = (
        db.query(models.PersonalRecord)
        .join(models.Exercise)
        .filter(models.PersonalRecord.user_telegram_id == user.telegram_id)
        .order_by(desc(models.PersonalRecord.updated_at))
        .all()
    )
    return {
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "photo_url": user.photo_url,
        "xp_total": user.xp_total or 0,
        **level_data,
        "personal_records": [
            {
                "id": record.id,
                "exercise_id": record.exercise_id,
                "exercise_name": record.exercise.name if record.exercise else "",
                "max_weight_kg": float(record.max_weight_kg),
                "max_reps": record.max_reps,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            }
            for record in records
        ],
    }
