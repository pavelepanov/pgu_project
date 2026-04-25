MEAL_ENTRY_XP = 10
WORKOUT_SET_XP = 5
XP_PER_LEVEL = 100


def xp_for_meal_entry() -> int:
    return MEAL_ENTRY_XP


def xp_for_workout_set() -> int:
    return WORKOUT_SET_XP


def calculate_level(xp_total: int) -> dict:
    safe_xp = max(xp_total or 0, 0)
    return {
        "level": safe_xp // XP_PER_LEVEL + 1,
        "xp_progress": safe_xp % XP_PER_LEVEL,
        "xp_to_next": XP_PER_LEVEL,
    }
