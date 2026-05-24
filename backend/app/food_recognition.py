"""
Модуль распознавания еды по фото через Google Gemini API.
Содержит детальное логирование для отладки и fallback для локальной разработки.
"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except Exception:
    genai = None  # type: ignore
    types = None  # type: ignore
    GENAI_AVAILABLE = False

from .config import get_settings

# ---------------------------------------------------------------------------
# Настройка логирования
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
settings = get_settings()

if not GENAI_AVAILABLE:
    logger.warning("⚠️ google.genai library not installed — Gemini features disabled.")

# Конфигурация Gemini
GEMINI_API_KEY = settings.gemini_api_key
GEMINI_MODEL = settings.gemini_model
USE_STUB = settings.use_gemini_stub

client = None
if GEMINI_API_KEY and GENAI_AVAILABLE:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("✅ Gemini client инициализирован успешно.")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Gemini client: {type(e).__name__}: {e}")
elif GEMINI_API_KEY and not GENAI_AVAILABLE:
    logger.warning("⚠️ GEMINI_API_KEY задан, но google.genai не установлен. Gemini недоступен.")
else:
    logger.warning("⚠️ GEMINI_API_KEY не найден. Проверьте .env и переменные окружения.")


async def recognize_food_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> Optional[Dict[str, Any]]:
    """
    Распознаёт блюдо по фотографии через Google Gemini.
    
    Args:
        image_bytes: Байты изображения
        mime_type: MIME-тип файла (по умолчанию image/jpeg)
        
    Returns:
        Словарь с данными о блюде или None, если распознать не удалось
    """
    logger.info(f" Начало распознавания. Размер файла: {len(image_bytes)} байт, тип: {mime_type}")

    # 🔹 Режим заглушки для локальной разработки
    if USE_STUB:
        logger.warning("🧪 Активирован режим USE_GEMINI_STUB. Возвращаю тестовые данные.")
        return {
            "food_name": "Куриная грудка на гриле (тест)",
            "calories_per_100g": 165.0,
            "protein_per_100g": 31.0,
            "fat_per_100g": 3.6,
            "carbs_per_100g": 0.0,
            "estimated_grams": 150,
            "confidence": "высокая"
        }

    if not client:
        logger.error("❌ Gemini client не инициализирован. Проверьте GEMINI_API_KEY.")
        return None

    # Промпт для строгого JSON-ответа
    prompt = """
Ты — эксперт по питанию и анализу изображений еды. Твоя задача — точно определить блюдо на фото и рассчитать его пищевую ценность.

Верни ответ СТРОГО в формате JSON без дополнительного текста, markdown или пояснений:
{
  "food_name": "Название блюда на русском",
  "calories_per_100g": 0.0,
  "protein_per_100g": 0.0,
  "fat_per_100g": 0.0,
  "carbs_per_100g": 0.0,
  "estimated_grams": 0,
  "confidence": "высокая|средняя|низкая"
}

Правила:
- Если блюдо не распознано или фото некачественное, верни: {"error": "Не удалось распознать блюдо"}
- Оценивай примерный вес порции в граммах (обычно 100-300г для основных блюд, 50-150г для гарниров)
- Учитывай способ приготовления (жарка увеличивает жиры, варка сохраняет нутриенты)
"""

    try:
        logger.info(f" Отправка запроса к модели: {GEMINI_MODEL}")
        
        # Вызываем API в отдельном потоке, чтобы не блокировать event loop
        response = await asyncio.to_thread(
            lambda: client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt
                ]
            )
        )
        
        raw_text = response.text
        logger.debug(f"📥 Сырой ответ от Gemini (первые 400 символов): {raw_text[:400]}...")

        # Очистка от markdown-блоков (```json ... ```)
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```"):
            parts = cleaned_text.split("```", 2)
            cleaned_text = parts[1].strip()
            if cleaned_text.lower().startswith("json"):
                cleaned_text = cleaned_text[4:].strip()
        
        logger.debug(f"🧹 Текст после очистки: {cleaned_text[:300]}...")

        # Парсинг JSON
        result = json.loads(cleaned_text)
        
        if "error" in result:
            logger.warning(f"⚠️ Gemini явно вернул ошибку: {result['error']}")
            return None
            
        if not result.get("food_name"):
            logger.warning("⚠️ В ответе отсутствует поле 'food_name'.")
            return None

        # Нормализация типов данных
        normalized = {
            "food_name": str(result.get("food_name", "Неизвестное блюдо")),
            "calories_per_100g": float(result.get("calories_per_100g", 0)),
            "protein_per_100g": float(result.get("protein_per_100g", 0)),
            "fat_per_100g": float(result.get("fat_per_100g", 0)),
            "carbs_per_100g": float(result.get("carbs_per_100g", 0)),
            "estimated_grams": int(result.get("estimated_grams", 100)),
            "confidence": str(result.get("confidence", "средняя"))
        }
        
        logger.info(f"✅ Успешно распознано: {normalized['food_name']} | {normalized['estimated_grams']}г | {normalized['confidence']}")
        return normalized

    except json.JSONDecodeError as e:
        logger.error(f"💥 Ошибка парсинга JSON: {e}")
        logger.error(f"📄 Не удалось распарсить ответ: {raw_text[:500]}")
        return None
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при вызове Gemini API: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def calculate_nutrition_values(recognized_data: Dict[str, Any]) -> Dict[str, float]:
    """Рассчитывает фактические значения КБЖУ на основе распознанных данных и веса порции."""
    grams = recognized_data.get("estimated_grams", 100)
    multiplier = grams / 100.0
    
    return {
        "calories": round(recognized_data["calories_per_100g"] * multiplier),
        "protein": round(recognized_data["protein_per_100g"] * multiplier, 2),
        "fat": round(recognized_data["fat_per_100g"] * multiplier, 2),
        "carbs": round(recognized_data["carbs_per_100g"] * multiplier, 2),
        "grams": grams
    }