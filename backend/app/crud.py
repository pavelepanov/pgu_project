from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app import models
from app.xp import calculate_level, xp_for_meal_entry, xp_for_workout_set


def _today_bounds() -> tuple[datetime, datetime]:
    today = datetime.now(UTC).date()
    start = datetime.combine(today, time.min, tzinfo=UTC)
    return start, start + timedelta(days=1)


def _date_range_bounds(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    if date_to < date_from:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_to must be after date_from")

    start = datetime.combine(date_from, time.min, tzinfo=UTC)
    end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC)
    return start, end


def _money(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _optional_money(value: Decimal | float | int | None) -> Decimal | None:
    return _money(value) if value is not None else None


def _macro(value_per_100g, grams: int) -> Decimal:
    return _money(Decimal(value_per_100g) * Decimal(grams) / Decimal(100))


def upsert_user_from_telegram(db: Session, telegram_user: dict) -> models.User:
    telegram_id = int(telegram_user["id"])
    user = db.get(models.User, telegram_id)
    if not user:
        user = models.User(telegram_id=telegram_id, first_name=telegram_user.get("first_name") or "User")
        db.add(user)

    user.first_name = telegram_user.get("first_name") or "User"
    user.last_name = telegram_user.get("last_name") or None
    user.username = telegram_user.get("username") or None
    user.photo_url = telegram_user.get("photo_url") or None
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        user = db.get(models.User, telegram_id)
        if user is None:
            raise
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
        "load_type": workout_set.exercise.load_type if workout_set.exercise else "",
        "muscle_group": workout_set.exercise.muscle_group if workout_set.exercise else "",
        "set_index": workout_set.set_index,
        "weight_kg": float(workout_set.weight_kg),
        "reps": workout_set.reps,
        "duration_min": float(workout_set.duration_min) if workout_set.duration_min is not None else None,
        "distance_km": float(workout_set.distance_km) if workout_set.distance_km is not None else None,
        "speed_kmh": float(workout_set.speed_kmh) if workout_set.speed_kmh is not None else None,
        "pace_min_per_km": float(workout_set.pace_min_per_km) if workout_set.pace_min_per_km is not None else None,
        "created_at": workout_set.created_at.isoformat() if workout_set.created_at else None,
    }


def serialize_workout(workout: models.Workout) -> dict:
    return {
        "id": workout.id,
        "title": workout.title,
        "performed_at": workout.performed_at.isoformat() if workout.performed_at else None,
        "sets": [serialize_set(workout_set) for workout_set in sorted(workout.sets, key=lambda item: item.set_index)],
    }


def serialize_workout_plan_exercise(item: models.WorkoutPlanExercise) -> dict:
    return {
        "id": item.id,
        "exercise_id": item.exercise_id,
        "exercise_name": item.exercise.name if item.exercise else "",
        "muscle_group": item.exercise.muscle_group if item.exercise else "",
        "load_type": item.exercise.load_type if item.exercise else "",
        "position": item.position,
        "target_sets": item.target_sets,
        "target_reps": item.target_reps,
        "target_weight_kg": float(item.target_weight_kg) if item.target_weight_kg is not None else None,
    }


def serialize_workout_plan(plan: models.WorkoutPlan) -> dict:
    exercises = sorted(plan.exercises, key=lambda item: item.position)
    return {
        "id": plan.id,
        "title": plan.title,
        "description": plan.description,
        "is_default": plan.is_default,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "exercises": [serialize_workout_plan_exercise(item) for item in exercises],
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


def _remove_xp(db: Session, user: models.User, source_type: str, source_id: int) -> None:
    xp_events = (
        db.query(models.XpEvent)
        .filter(
            models.XpEvent.user_telegram_id == user.telegram_id,
            models.XpEvent.source_type == source_type,
            models.XpEvent.source_id == source_id,
        )
        .all()
    )
    for event in xp_events:
        user.xp_total = max(0, (user.xp_total or 0) - event.xp_amount)
        db.delete(event)


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


def find_similar_food(db: Session, food_name: str) -> dict | None:
    if not food_name:
        return None
    pattern = f"%{food_name.strip()}%"
    product = (
        db.query(models.FoodProduct)
        .filter(models.FoodProduct.is_active.is_(True), models.FoodProduct.name.ilike(pattern))
        .order_by(models.FoodProduct.name)
        .first()
    )
    if not product:
        return None
    return {
        "id": product.id,
        "name": product.name,
        "brand": product.brand,
        "calories_per_100g": float(product.calories_per_100g),
        "protein_per_100g": float(product.protein_per_100g),
        "fat_per_100g": float(product.fat_per_100g),
        "carbs_per_100g": float(product.carbs_per_100g),
        "default_grams": product.default_grams,
    }


def create_manual_meal_entry(db: Session, user: models.User, payload) -> dict:
    entry = models.MealEntry(
        user_telegram_id=user.telegram_id,
        product_id=None,
        meal_type=payload.meal_type,
        product_name=payload.product_name.strip(),
        grams=payload.grams,
        calories=payload.calories,
        protein=_money(payload.protein),
        fat=_money(payload.fat),
        carbs=_money(payload.carbs),
    )
    db.add(entry)
    db.flush()
    _add_xp(db, user, "manual_meal_entry", entry.id, xp_for_meal_entry())
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
    db.flush()
    _remove_xp(db, user, "meal_entry", entry.id)
    _remove_xp(db, user, "manual_meal_entry", entry.id)
    db.commit()
    db.refresh(user)
    return {"nutrition": get_today_nutrition(db, user), "profile": get_profile(db, user)}


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


def get_workout_plans(db: Session, user: models.User) -> list[dict]:
    plans = (
        db.query(models.WorkoutPlan)
        .filter(
            or_(
                models.WorkoutPlan.is_default.is_(True),
                models.WorkoutPlan.user_telegram_id == user.telegram_id,
            )
        )
        .order_by(desc(models.WorkoutPlan.is_default), desc(models.WorkoutPlan.created_at), models.WorkoutPlan.title)
        .all()
    )
    return [serialize_workout_plan(plan) for plan in plans]


def create_workout_plan(db: Session, user: models.User, payload) -> dict:
    exercise_ids = [item.exercise_id for item in payload.exercises]
    exercises = (
        db.query(models.Exercise)
        .filter(models.Exercise.id.in_(exercise_ids), models.Exercise.is_active.is_(True))
        .all()
    )
    found_ids = {exercise.id for exercise in exercises}
    missing_ids = sorted(set(exercise_ids) - found_ids)
    if missing_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Exercises not found: {missing_ids}")

    plan = models.WorkoutPlan(
        user_telegram_id=user.telegram_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        is_default=False,
    )
    db.add(plan)
    db.flush()

    for position, item in enumerate(payload.exercises, start=1):
        db.add(
            models.WorkoutPlanExercise(
                plan_id=plan.id,
                exercise_id=item.exercise_id,
                position=position,
                target_sets=item.target_sets,
                target_reps=item.target_reps,
                target_weight_kg=_money(item.target_weight_kg) if item.target_weight_kg is not None else None,
            )
        )

    db.commit()
    db.refresh(plan)
    return serialize_workout_plan(plan)


def start_workout_plan(db: Session, user: models.User, plan_id: int) -> dict:
    plan = (
        db.query(models.WorkoutPlan)
        .filter(
            models.WorkoutPlan.id == plan_id,
            or_(
                models.WorkoutPlan.is_default.is_(True),
                models.WorkoutPlan.user_telegram_id == user.telegram_id,
            ),
        )
        .one_or_none()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout plan not found")

    workout = models.Workout(user_telegram_id=user.telegram_id, title=plan.title)
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return {"workout": serialize_workout(workout), "plan": serialize_workout_plan(plan)}


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
    if workout_set.exercise and workout_set.exercise.load_type != "силовая":
        return
    if Decimal(workout_set.weight_kg or 0) <= 0:
        return

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


def _recalculate_personal_record(db: Session, user: models.User, exercise_id: int) -> None:
    exercise = db.get(models.Exercise, exercise_id)
    if not exercise or exercise.load_type != "силовая":
        return

    workout_sets = (
        db.query(models.WorkoutSet)
        .join(models.Workout)
        .filter(
            models.Workout.user_telegram_id == user.telegram_id,
            models.WorkoutSet.exercise_id == exercise_id,
            models.WorkoutSet.weight_kg > 0,
        )
        .all()
    )

    record = (
        db.query(models.PersonalRecord)
        .filter(
            models.PersonalRecord.user_telegram_id == user.telegram_id,
            models.PersonalRecord.exercise_id == exercise_id,
        )
        .one_or_none()
    )

    if not workout_sets:
        if record:
            db.delete(record)
        return

    max_weight = max((Decimal(item.weight_kg or 0) for item in workout_sets), default=Decimal(0))
    max_reps = max((item.reps or 0 for item in workout_sets), default=0)

    if not record:
        db.add(
            models.PersonalRecord(
                user_telegram_id=user.telegram_id,
                exercise_id=exercise_id,
                max_weight_kg=max_weight,
                max_reps=max_reps,
            )
        )
        return

    record.max_weight_kg = max_weight
    record.max_reps = max_reps


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
        exercise=exercise,
        set_index=next_index,
        weight_kg=_money(payload.weight_kg),
        reps=payload.reps,
        duration_min=_optional_money(payload.duration_min),
        distance_km=_optional_money(payload.distance_km),
        speed_kmh=_optional_money(payload.speed_kmh),
        pace_min_per_km=_optional_money(payload.pace_min_per_km),
    )
    db.add(workout_set)
    db.flush()
    _update_personal_record(db, user, workout_set)
    _add_xp(db, user, "workout_set", workout_set.id, xp_for_workout_set())
    db.commit()
    db.refresh(workout)
    db.refresh(user)
    return {"workout": serialize_workout(workout), "profile": get_profile(db, user)}


def delete_workout_set(db: Session, user: models.User, set_id: int) -> dict:
    workout_set = (
        db.query(models.WorkoutSet)
        .join(models.Workout)
        .filter(models.WorkoutSet.id == set_id, models.Workout.user_telegram_id == user.telegram_id)
        .one_or_none()
    )
    if not workout_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout set not found")

    workout = workout_set.workout
    exercise_id = workout_set.exercise_id
    db.delete(workout_set)
    db.flush()
    _recalculate_personal_record(db, user, exercise_id)
    _remove_xp(db, user, "workout_set", set_id)
    db.commit()
    db.refresh(user)
    return {"workouts": get_today_workouts(db, user), "profile": get_profile(db, user)}


def update_profile(db: Session, user: models.User, payload) -> dict:
    payload_data = payload.dict(exclude_unset=True)
    if "height_cm" in payload_data:
        user.height_cm = payload_data["height_cm"]
    if "weight_kg" in payload_data:
        user.weight_kg = _optional_money(payload_data["weight_kg"])
    if "age" in payload_data:
        user.age = payload_data["age"]
    if "fitness_goal" in payload_data:
        user.fitness_goal = payload_data["fitness_goal"]
    if "protein_target" in payload_data:
        user.protein_target = payload_data["protein_target"]
    if "fat_target" in payload_data:
        user.fat_target = payload_data["fat_target"]
    if "carbs_target" in payload_data:
        user.carbs_target = payload_data["carbs_target"]

    db.add(user)
    db.commit()
    db.refresh(user)
    return get_profile(db, user)


def delete_user_account(db: Session, user: models.User) -> dict:
    db.query(models.XpEvent).filter(models.XpEvent.user_telegram_id == user.telegram_id).delete(synchronize_session=False)
    db.query(models.WorkoutPlanExercise).filter(
        models.WorkoutPlanExercise.plan_id.in_(
            db.query(models.WorkoutPlan.id).filter(models.WorkoutPlan.user_telegram_id == user.telegram_id)
        )
    ).delete(synchronize_session=False)
    db.query(models.WorkoutPlan).filter(models.WorkoutPlan.user_telegram_id == user.telegram_id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    return {"deleted": True}


# backend/app/crud.py

from app.models import User
from app.schemas import RegisterRequest  # убедитесь, что схема импортирована

def complete_registration(db: Session, user: User, payload: RegisterRequest) -> dict:
    """
    Завершает регистрацию пользователя: обновляет профиль и устанавливает флаг.
    """
    # Обновляем поля профиля из payload
    if payload.height_cm is not None:
        user.height_cm = payload.height_cm
    if payload.weight_kg is not None:
        user.weight_kg = payload.weight_kg
    if payload.age is not None:
        user.age = payload.age
    if payload.fitness_goal is not None:
        user.fitness_goal = payload.fitness_goal
    
    # 🔥 ГЛАВНОЕ: устанавливаем флаг завершения регистрации
    user.registration_complete = True
    
    # Сохраняем изменения
    db.commit()
    db.refresh(user)
    
    # Возвращаем полный профиль (как в get_profile)
    return get_profile(db, user)


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


def get_stats(db: Session, user: models.User, date_from: date, date_to: date) -> dict:
    start, end = _date_range_bounds(date_from, date_to)
    meal_entries = (
        db.query(models.MealEntry)
        .filter(
            models.MealEntry.user_telegram_id == user.telegram_id,
            models.MealEntry.eaten_at >= start,
            models.MealEntry.eaten_at < end,
        )
        .order_by(models.MealEntry.eaten_at)
        .all()
    )
    workout_sets = (
        db.query(models.WorkoutSet)
        .join(models.Workout)
        .join(models.Exercise)
        .filter(
            models.Workout.user_telegram_id == user.telegram_id,
            models.Workout.performed_at >= start,
            models.Workout.performed_at < end,
        )
        .order_by(models.Workout.performed_at, models.WorkoutSet.id)
        .all()
    )
    workouts_count = (
        db.query(func.count(models.Workout.id))
        .filter(
            models.Workout.user_telegram_id == user.telegram_id,
            models.Workout.performed_at >= start,
            models.Workout.performed_at < end,
        )
        .scalar()
        or 0
    )
    tracking_entries = (
        db.query(models.DailyTracking)
        .filter(
            models.DailyTracking.user_telegram_id == user.telegram_id,
            models.DailyTracking.tracked_date >= date_from,
            models.DailyTracking.tracked_date <= date_to,
        )
        .order_by(models.DailyTracking.tracked_date)
        .all()
    )

    nutrition_days: dict[str, dict] = {}
    for entry in meal_entries:
        day = entry.eaten_at.date().isoformat()
        if day not in nutrition_days:
            nutrition_days[day] = {"date": day, "calories": 0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
        nutrition_days[day]["calories"] += entry.calories
        nutrition_days[day]["protein"] += float(entry.protein)
        nutrition_days[day]["fat"] += float(entry.fat)
        nutrition_days[day]["carbs"] += float(entry.carbs)

    strength_by_exercise: dict[int, dict] = {}
    for workout_set in workout_sets:
        item = strength_by_exercise.setdefault(
            workout_set.exercise_id,
            {
                "exercise_id": workout_set.exercise_id,
                "exercise_name": workout_set.exercise.name if workout_set.exercise else "",
                "muscle_group": workout_set.exercise.muscle_group if workout_set.exercise else "",
                "load_type": workout_set.exercise.load_type if workout_set.exercise else "",
                "max_weight_kg": 0.0,
                "max_reps": 0,
                "sets": 0,
                "volume_kg": 0.0,
                "duration_min": 0.0,
                "distance_km": 0.0,
                "best_speed_kmh": 0.0,
                "best_pace_min_per_km": None,
            },
        )
        weight = float(workout_set.weight_kg)
        item["max_weight_kg"] = max(item["max_weight_kg"], weight)
        item["max_reps"] = max(item["max_reps"], workout_set.reps)
        item["sets"] += 1
        item["volume_kg"] += round(weight * workout_set.reps, 2)
        item["duration_min"] += float(workout_set.duration_min or 0)
        item["distance_km"] += float(workout_set.distance_km or 0)
        item["best_speed_kmh"] = max(item["best_speed_kmh"], float(workout_set.speed_kmh or 0))
        if workout_set.pace_min_per_km is not None:
            pace = float(workout_set.pace_min_per_km)
            if item["best_pace_min_per_km"] is None or pace < item["best_pace_min_per_km"]:
                item["best_pace_min_per_km"] = pace

    tracking_days = [
        {
            "date": item.tracked_date.isoformat(),
            "sleep_hours": float(item.sleep_hours) if item.sleep_hours is not None else 0,
            "water_liters": float(item.water_liters) if item.water_liters is not None else 0,
        }
        for item in tracking_entries
    ]
    tracking_sleep_values = [item["sleep_hours"] for item in tracking_days if item["sleep_hours"] > 0]
    tracking_water_values = [item["water_liters"] for item in tracking_days if item["water_liters"] > 0]

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "nutrition": {
            "totals": {
                "calories": sum(entry.calories for entry in meal_entries),
                "protein": round(sum(float(entry.protein) for entry in meal_entries), 1),
                "fat": round(sum(float(entry.fat) for entry in meal_entries), 1),
                "carbs": round(sum(float(entry.carbs) for entry in meal_entries), 1),
            },
            "days": [
                {
                    **day,
                    "protein": round(day["protein"], 1),
                    "fat": round(day["fat"], 1),
                    "carbs": round(day["carbs"], 1),
                }
                for day in nutrition_days.values()
            ],
        },
        "strength": {
            "total_workouts": workouts_count,
            "total_sets": len(workout_sets),
            "exercises": sorted(
                strength_by_exercise.values(),
                key=lambda item: (item["sets"], item["max_weight_kg"]),
                reverse=True,
            ),
        },
        "tracking": {
            "totals": {
                "sleep_hours": round(sum(tracking_sleep_values), 1),
                "water_liters": round(sum(tracking_water_values), 1),
                "avg_sleep_hours": round(sum(tracking_sleep_values) / len(tracking_sleep_values), 1) if tracking_sleep_values else 0,
                "avg_water_liters": round(sum(tracking_water_values) / len(tracking_water_values), 1) if tracking_water_values else 0,
            },
            "days": tracking_days,
        },
    }


def get_exercise_stats(db: Session, user: models.User, exercise_id: int, date_from: date, date_to: date) -> dict:
    exercise = db.get(models.Exercise, exercise_id)
    if not exercise or not exercise.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    start, end = _date_range_bounds(date_from, date_to)
    workout_sets = (
        db.query(models.WorkoutSet)
        .join(models.Workout)
        .filter(
            models.Workout.user_telegram_id == user.telegram_id,
            models.WorkoutSet.exercise_id == exercise_id,
            models.Workout.performed_at >= start,
            models.Workout.performed_at < end,
        )
        .order_by(models.Workout.performed_at, models.WorkoutSet.id)
        .all()
    )

    days: dict[str, dict] = {}
    for workout_set in workout_sets:
        performed_date = workout_set.workout.performed_at.date().isoformat()
        item = days.setdefault(
            performed_date,
            {
                "date": performed_date,
                "sets": 0,
                "max_weight_kg": 0.0,
                "max_reps": 0,
                "volume_kg": 0.0,
                "duration_min": 0.0,
                "distance_km": 0.0,
                "best_speed_kmh": 0.0,
                "best_pace_min_per_km": None,
            },
        )
        weight = float(workout_set.weight_kg or 0)
        item["sets"] += 1
        item["max_weight_kg"] = max(item["max_weight_kg"], weight)
        item["max_reps"] = max(item["max_reps"], workout_set.reps)
        item["volume_kg"] += round(weight * workout_set.reps, 2)
        item["duration_min"] += float(workout_set.duration_min or 0)
        item["distance_km"] += float(workout_set.distance_km or 0)
        item["best_speed_kmh"] = max(item["best_speed_kmh"], float(workout_set.speed_kmh or 0))
        if workout_set.pace_min_per_km is not None:
            pace = float(workout_set.pace_min_per_km)
            if item["best_pace_min_per_km"] is None or pace < item["best_pace_min_per_km"]:
                item["best_pace_min_per_km"] = pace

    history = list(days.values())
    return {
        "exercise": serialize_exercise(exercise),
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "history": history,
        "sets": [serialize_set(workout_set) for workout_set in workout_sets],
    }


def get_date_nutrition(db: Session, user: models.User, target_date: date) -> dict:
    """Get nutrition data for a specific date."""
    start = datetime.combine(target_date, time.min, tzinfo=UTC)
    end = start + timedelta(days=1)

    entries = (
        db.query(models.MealEntry)
        .filter(
            models.MealEntry.user_telegram_id == user.telegram_id,
            models.MealEntry.eaten_at >= start,
            models.MealEntry.eaten_at < end,
        )
        .order_by(models.MealEntry.eaten_at)
        .all()
    )

    totals = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
    for entry in entries:
        totals["calories"] += entry.calories
        totals["protein"] += float(entry.protein)
        totals["fat"] += float(entry.fat)
        totals["carbs"] += float(entry.carbs)

    return {
        "date": target_date.isoformat(),
        "entries": [serialize_meal(entry) for entry in entries],
        "totals": totals,
    }


def get_date_workouts(db: Session, user: models.User, target_date: date) -> dict:
    """Get workouts data for a specific date."""
    start = datetime.combine(target_date, time.min, tzinfo=UTC)
    end = start + timedelta(days=1)

    workouts = (
        db.query(models.Workout)
        .filter(
            models.Workout.user_telegram_id == user.telegram_id,
            models.Workout.performed_at >= start,
            models.Workout.performed_at < end,
        )
        .order_by(models.Workout.performed_at)
        .all()
    )

    return {
        "date": target_date.isoformat(),
        "workouts": [serialize_workout(workout) for workout in workouts],
        "total_sets": sum(len(w.sets) for w in workouts),
    }


def get_date_tracking(db: Session, user: models.User, target_date: date) -> dict:
    """Get tracking data (sleep, water) for a specific date."""
    tracking = (
        db.query(models.DailyTracking)
        .filter(
            models.DailyTracking.user_telegram_id == user.telegram_id,
            models.DailyTracking.tracked_date == target_date,
        )
        .one_or_none()
    )

    return {
        "date": target_date.isoformat(),
        "sleep_hours": float(tracking.sleep_hours) if tracking and tracking.sleep_hours else 0,
        "water_liters": float(tracking.water_liters) if tracking and tracking.water_liters else 0,
    }


def get_today_tracking(db: Session, user: models.User) -> dict:
    """Get today's tracking data."""
    today = datetime.now(UTC).date()
    return get_date_tracking(db, user, today)


def _calculate_bmi(user: models.User) -> float | None:
    if not user.height_cm or user.weight_kg is None:
        return None
    height_m = Decimal(user.height_cm) / Decimal(100)
    if height_m <= 0:
        return None
    return float((Decimal(user.weight_kg) / (height_m * height_m)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _default_calorie_target(user: models.User) -> int:
    """
    Рассчитывает дневную норму калорий на основе ИМТ, веса и цели.
    Использует адаптированные коэффициенты Миффлина-Сент-Жеора.
    """
    if user.weight_kg is None:
        return 1800

    weight = float(user.weight_kg)
    bmi = _calculate_bmi(user) or 22.0
    goal = (user.fitness_goal or "maintain").lower()

    # Базовый расход (Миффлин-Сент-Жеор) в расчёте на кг веса
    # Примерно 25-32 ккал/кг в зависимости от ИМТ и активности
    if goal == "lose":
        # Похудение: дефицит калорий, но не менее 1.2 от BMR
        # Коэффициент зависит от текущего ИМТ
        if bmi >= 30:  # Ожирение
            multiplier = 20  # Дефицит 20%, может быть больше
        elif bmi >= 25:  # Избыточный вес
            multiplier = 23  # Дефицит 15%
        else:  # Норма или недостаток веса
            multiplier = 25  # Дефицит 10%
    elif goal == "gain":
        # Набор массы: профицит калорий, +300-500 сверх нормы
        if bmi < 18.5:  # Недостаточный вес - агрессивный набор
            multiplier = 37  # +25% от нормы
        else:  # Нормальный вес - умеренный набор
            multiplier = 35  # +15% от нормы
    else:  # maintain
        # Поддержание: норма 28-32 ккал/кг
        if bmi >= 30:
            multiplier = 28
        elif bmi >= 25:
            multiplier = 30
        else:
            multiplier = 32

    # Финальный расчёт с минимальной границей
    target = int(round(weight * multiplier))
    return max(1200, min(target, 4000))  # Границы: 1200-4000 ккал


def _default_macro_targets(user: models.User, calorie_target: int) -> dict[str, int]:
    if user.weight_kg is None:
        return {"protein": 120, "fat": 70, "carbs": 220}

    weight = float(user.weight_kg)
    goal = (user.fitness_goal or "maintain").lower()
    protein_per_kg = 2.2 if goal == "gain" else 2.0
    fat_per_kg = 1.0 if goal != "lose" else 0.9

    protein = max(50, int(round(weight * protein_per_kg)))
    fat = max(30, int(round(weight * fat_per_kg)))
    carbs = max(0, int(round((calorie_target - protein * 4 - fat * 9) / 4)))

    if carbs < 20:
        carbs = 20
    return {"protein": protein, "fat": fat, "carbs": carbs}


def _get_macro_targets(user: models.User, calorie_target: int) -> dict[str, int]:
    default_targets = _default_macro_targets(user, calorie_target)
    return {
        "protein": int(user.protein_target) if user.protein_target is not None else default_targets["protein"],
        "fat": int(user.fat_target) if user.fat_target is not None else default_targets["fat"],
        "carbs": int(user.carbs_target) if user.carbs_target is not None else default_targets["carbs"],
    }


def get_profile(db: Session, user: models.User) -> dict:
    level_data = calculate_level(user.xp_total or 0)
    bmi = None
    if user.height_cm and user.weight_kg is not None:
        height_m = Decimal(user.height_cm) / Decimal(100)
        if height_m > 0:
            bmi = float((Decimal(user.weight_kg) / (height_m * height_m)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

    records = (
        db.query(models.PersonalRecord)
        .join(models.Exercise)
        .filter(models.PersonalRecord.user_telegram_id == user.telegram_id)
        .order_by(desc(models.PersonalRecord.updated_at))
        .all()
    )
    calorie_target = _default_calorie_target(user)
    macro_targets = _get_macro_targets(user, calorie_target)

    return {
        "telegram_id": user.telegram_id,
        "registration_complete": user.registration_complete,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "photo_url": user.photo_url,
        "height_cm": user.height_cm,
        "weight_kg": float(user.weight_kg) if user.weight_kg is not None else None,
        "age": user.age,
        "fitness_goal": user.fitness_goal or "maintain",
        "calorie_target": calorie_target,
        "protein_target": macro_targets["protein"],
        "fat_target": macro_targets["fat"],
        "carbs_target": macro_targets["carbs"],
        "bmi": bmi,
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
