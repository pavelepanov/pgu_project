"""AI-powered daily summary generation using g4f"""
import json
from datetime import datetime, UTC


async def generate_daily_summary(user, nutrition_data: dict, workouts_data: dict, tracking_data: dict) -> str:
    """
    Generate AI-powered daily summary using g4f (free AI service)
    
    Args:
        user: User object with profile info
        nutrition_data: Today's nutrition data from get_today_nutrition
        workouts_data: Today's workouts data from get_today_workouts
        tracking_data: Sleep and water tracking data
        
    Returns:
        AI-generated summary text
    """
    try:
        import g4f
    except ImportError:
        # Fallback if g4f not installed
        return _generate_fallback_summary(user, nutrition_data, workouts_data, tracking_data)
    
    # Prepare context for AI
    context = _prepare_summary_context(user, nutrition_data, workouts_data, tracking_data)
    
    prompt = f"""Ты фитнес-коуч и диетолог. Основываясь на данных пользователя за сегодня, 
дай краткую, мотивирующую сводку (2-3 предложения) на русском языке.

Данные пользователя:
{context}

Дай конкретные, практичные советы. Не используй вводные фразы вроде "Вот сводка" или "Итак".
Начни сразу с анализа."""
    
    try:
        # Use g4f to generate response
        response = await g4f.ChatCompletion.create_async(
            model="gpt-4-free",
            messages=[{"role": "user", "content": prompt}],
            timeout=10,
        )
        
        if isinstance(response, str):
            return response.strip()
        
        return str(response).strip()
    except Exception as e:
        print(f"AI generation failed: {e}")
        return _generate_fallback_summary(user, nutrition_data, workouts_data, tracking_data)


def _prepare_summary_context(user, nutrition_data: dict, workouts_data: dict, tracking_data: dict) -> str:
    """Prepare data context for AI analysis"""
    today = datetime.now(UTC).date().isoformat()
    
    # Nutrition info
    totals = nutrition_data.get("totals", {})
    cal_per_100g = 2000  # typical daily target
    cal_percent = int((totals.get("calories", 0) / cal_per_100g) * 100)
    
    # Workouts info
    total_sets = workouts_data.get("total_sets", 0)
    workouts_count = len(workouts_data.get("workouts", []))
    
    # Personal info
    name = user.first_name if hasattr(user, 'first_name') else "Тренер"
    level = 1  # default, calculate if available
    
    context = f"""
Имя: {name}
Дата: {today}
Уровень: {level}

📊 Питание:
- Калории: {totals.get('calories', 0)}/{cal_per_100g} ({cal_percent}%)
- Белки: {totals.get('protein', 0)}г
- Жиры: {totals.get('fat', 0)}г
- Углеводы: {totals.get('carbs', 0)}г
- Приемов пищи: {len(nutrition_data.get('entries', []))}

💪 Тренировки:
- Подходов: {total_sets}
- Тренировок: {workouts_count}

😴 Отслеживание:
- Сон: {tracking_data.get('sleep_hours', 'не указан')} ч
- Вода: {tracking_data.get('water_liters', 'не указана')} л
"""
    return context.strip()


def _generate_fallback_summary(user, nutrition_data: dict, workouts_data: dict, tracking_data: dict) -> str:
    """Generate simple summary without AI as fallback"""
    totals = nutrition_data.get("totals", {})
    total_sets = workouts_data.get("total_sets", 0)
    sleep = tracking_data.get("sleep_hours")
    water = tracking_data.get("water_liters")
    
    parts = []
    
    # Calories comment
    cal = totals.get("calories", 0)
    if cal > 2200:
        parts.append(f"Сегодня ты получил {cal} ккал - это чуть выше нормы. В следующий раз постарайся придерживаться нормы.")
    elif cal > 1800:
        parts.append(f"Отличное питание! {cal} ккал в норме.")
    elif cal > 0:
        parts.append(f"Всего {cal} ккал - советуем добавить питательного.")
    
    # Workouts comment
    if total_sets > 8:
        parts.append(f"Мощная тренировка на {total_sets} подходов! Так держать!")
    elif total_sets > 0:
        parts.append(f"Хороший прогресс: {total_sets} подходов выполнено.")
    else:
        parts.append("Помни про тренировку - даже 20 минут активности пойдут на пользу.")
    
    # Sleep comment
    if sleep:
        if float(sleep) >= 7:
            parts.append(f"Отличный сон: {sleep} часов - восстанавливайся активно!")
        elif float(sleep) >= 6:
            parts.append(f"Норма сна: {sleep} ч - достаточно для восстановления.")
    
    return " ".join(parts)
