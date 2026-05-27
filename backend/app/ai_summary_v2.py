import asyncio
import os
import g4f

# Проверяем, что библиотека установлена
try:
    HAS_G4F = True
except ImportError:
    HAS_G4F = False

AI_SUMMARY_ENABLED = os.getenv("AI_SUMMARY_ENABLED", "false").lower() in ("1", "true", "yes")
AI_SUMMARY_PROVIDER = os.getenv("AI_SUMMARY_PROVIDER", "gpt-3.5-turbo").strip()
AI_SUMMARY_TIMEOUT_SECONDS = int(os.getenv("AI_SUMMARY_TIMEOUT_SECONDS", "10"))


def _use_external_ai() -> bool:
    return AI_SUMMARY_ENABLED and HAS_G4F and bool(AI_SUMMARY_PROVIDER)


def format_nutrition_summary(entries: list, totals: dict) -> str:
    meals_by_type = {}
    for entry in entries:
        meal_type = entry.get("meal_type", "unknown")
        if meal_type not in meals_by_type:
            meals_by_type[meal_type] = []
        meals_by_type[meal_type].append(
            f"{entry.get('product_name')} ({entry.get('grams')}г, {entry.get('calories')} ккал)"
        )

    summary = f"Питание: {totals.get('calories', 0)} ккал съедено"
    if totals.get("protein"): summary += f", белки {totals.get('protein')}г"
    if totals.get("fat"): summary += f", жиры {totals.get('fat')}г"
    if totals.get("carbs"): summary += f", углеводы {totals.get('carbs')}г"

    for meal_type, items in meals_by_type.items():
        summary += f". {meal_type.capitalize()}: {', '.join(items)}"
    return summary


def format_workout_summary(workouts_data: dict) -> str:
    workouts = workouts_data.get("workouts", []) if isinstance(workouts_data, dict) else workouts_data
    if not workouts:
        return "Тренировка: без активности"
    total_sets = sum(len(w.get("sets", [])) for w in workouts)
    titles = ", ".join(w.get("title", "Тренировка") for w in workouts)
    return f"Тренировка: {total_sets} подходов выполнено ({titles})"


def format_tracking_summary(tracking: dict) -> str:
    parts = []
    if tracking.get("sleep_hours"): parts.append(f"{tracking.get('sleep_hours')}ч сна")
    if tracking.get("water_liters"): parts.append(f"{tracking.get('water_liters')}л воды")
    return "Трекинг: " + (", ".join(parts) if parts else "без данных")


def _rule_based_daily(nutrition: dict, workouts: dict, tracking: dict, profile: dict) -> str:
    """Умная авто-сводка, если ИИ недоступен. Никогда не падает."""
    totals = nutrition.get("totals", {})
    cal, prot = totals.get("calories", 0), totals.get("protein", 0)
    goal = profile.get("fitness_goal", "maintain")
    w_count = len(workouts.get("workouts", []))
    sleep, water = tracking.get("sleep_hours", 0), tracking.get("water_liters", 0)
    xp = profile.get("xp_total", 0)

    tips = []
    if goal == "lose" and cal > 2200: tips.append("📉 Калории выше цели — завтра снизь углеводы.")
    elif goal == "gain" and cal < 1800: tips.append("📈 Для массы нужно больше энергии, добавь перекус.")
    elif prot < 60: tips.append("🥩 Белка маловато, добавь курицу или творог.")
    if w_count == 0: tips.append("🏋️ Сегодня без тренировки, завтра начни с базы.")
    elif w_count > 0: tips.append("💪 Отличная работа! Подходы записаны, XP начислен.")
    if sleep and sleep < 7: tips.append("😴 Сон короче 7ч — восстановление замедляется.")
    if water and water < 2: tips.append("💧 Пей больше воды, минимум 2 литра в день.")

    msg = f"📊 Сводка: {cal} ккал, {prot}г белка, {w_count} тренировок, {xp} XP.\n"
    return msg + ("\n".join(tips) if tips else "✅ Всё в балансе! Продолжай в том же духе.")


async def generate_daily_summary(nutrition: dict, workouts: dict, tracking: dict, profile: dict) -> str:
    nutrition_text = format_nutrition_summary(nutrition.get("entries", []), nutrition.get("totals", {}))
    workout_text = format_workout_summary(workouts)
    tracking_text = format_tracking_summary(tracking)

    prompt = f"""Ты - фитнес-ассистент. Короткая мотивирующая сводка на русском.
Данные:
- Цель: {profile.get('fitness_goal', 'поддержание')}
- {nutrition_text}
- {workout_text}
- {tracking_text}
- XP: {profile.get('xp_total', 0)}
2-3 предложения с эмодзи, оценка прогресса + 1 совет."""

    if not _use_external_ai():
        return _rule_based_daily(nutrition, workouts, tracking, profile)

    try:
        # ✅ Универсальный вызов, работает в большинстве версий g4f
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: g4f.ChatCompletion.create(
                    model=AI_SUMMARY_PROVIDER,
                    messages=[{"role": "user", "content": prompt}]
                )
            ),
            timeout=AI_SUMMARY_TIMEOUT_SECONDS,
        )
        if isinstance(response, str) and len(response.strip()) > 10:
            return response.strip()
        raise ValueError("Empty response")
    except Exception:
        # 🛡️ Fallback: авто-сводка на основе данных
        return _rule_based_daily(nutrition, workouts, tracking, profile)


async def generate_period_summary(
    nutrition_list: list, workouts_list: list, tracking_list: list, profile: dict, days: int = 7
) -> str:
    total_cal = sum(n.get("totals", {}).get("calories", 0) for n in nutrition_list)
    total_w = sum(len(w.get("workouts", [])) for w in workouts_list)
    avg_sleep = sum(t.get("sleep_hours", 0) for t in tracking_list) / max(len(tracking_list), 1)
    avg_water = sum(t.get("water_liters", 0) for t in tracking_list) / max(len(tracking_list), 1)

    prompt = f"""Анализ за {days} дней:
- Калории: {total_cal}, Тренировок: {total_w}
- Сон: {avg_sleep:.1f}ч, Вода: {avg_water:.1f}л
- Цель: {profile.get('fitness_goal')}
Вывод + 1 рекомендация, 3-4 предложения."""

    if not _use_external_ai():
        return f"📅 За {days} дней: {total_cal} ккал, {total_w} тренировок. Сон {avg_sleep:.1f}ч, вода {avg_water:.1f}л. {'✅ Хороший ритм!' if total_w >= 3 else '📈 Добавь активности на следующей неделе.'}"

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: g4f.ChatCompletion.create(
                    model=AI_SUMMARY_PROVIDER,
                    messages=[{"role": "user", "content": prompt}]
                )
            ),
            timeout=AI_SUMMARY_TIMEOUT_SECONDS,
        )
        if isinstance(response, str) and len(response.strip()) > 10:
            return response.strip()
        raise ValueError("Empty")
    except Exception:
        return f"📅 За {days} дней: {total_cal} ккал, {total_w} тренировок. Сон {avg_sleep:.1f}ч, вода {avg_water:.1f}л. {'✅ Хороший ритм!' if total_w >= 3 else '📈 Добавь активности на следующей неделе.'}"
