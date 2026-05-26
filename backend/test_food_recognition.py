#!/usr/bin/env python3
"""
🍽️ Standalone-скрипт для распознавания еды по фото через Google Gemini.
Запуск: python test_food_recognition.py path/to/photo.jpg
"""

import os
import sys
import json
import asyncio
import mimetypes
from pathlib import Path

# Добавляем parent-директорию в path, чтобы импортировать из app/
sys.path.insert(0, str(Path(__file__).parent))

from google import genai
from google.genai import types


def load_env_file(env_path=".env"):
    """Простая загрузка .env без внешних зависимостей."""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    # Убираем ${...} если есть
                    if value.startswith("${") and value.endswith("}"):
                        value = value[2:-1]
                    env_vars[key] = value
    return env_vars


async def recognize_food(image_path: str, api_key: str) -> dict:
    """Распознаёт еду по изображению через Gemini."""
    
    # Проверка файла
    if not os.path.exists(image_path):
        return {"error": f"Файл не найден: {image_path}"}
    
    # Определяем MIME-тип
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/jpeg"  # fallback
    
    # Читаем файл
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    print(f"📦 Загружено изображение: {os.path.basename(image_path)}")
    print(f"   Размер: {len(image_bytes) / 1024:.1f} КБ, тип: {mime_type}")
    
    # Инициализация клиента
    client = genai.Client(api_key=api_key)
    
    # Промпт для строгого JSON
    prompt = """
Ты — эксперт по питанию. Проанализируй изображение еды и определи блюдо.

Верни ТОЛЬКО валидный JSON без пояснений, без markdown:
{
  "food_name": "название на русском",
  "calories_per_100g": 0,
  "protein_per_100g": 0.0,
  "fat_per_100g": 0.0,
  "carbs_per_100g": 0.0,
  "estimated_grams": 0,
  "confidence": "высокая|средняя|низкая"
}

Если не можешь определить — верни: {"error": "Не распознано"}
"""
    
    try:
        print("📤 Отправляю запрос к Gemini...")
        
        response = await asyncio.to_thread(
            lambda: client.models.generate_content(
                model="gemini-2",
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt
                ]
            )
        )
        
        raw = response.text.strip()
        print(f"📥 Получен ответ ({len(raw)} символов)")
        
        # Очистка от markdown
        if raw.startswith("```"):
            parts = raw.split("```", 2)
            raw = parts[1].strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        
        # Парсинг JSON
        result = json.loads(raw)
        
        if "error" in result:
            return {"error": result["error"]}
        
        # Нормализация
        return {
            "food_name": str(result.get("food_name", "Неизвестно")),
            "calories_per_100g": float(result.get("calories_per_100g", 0)),
            "protein_per_100g": float(result.get("protein_per_100g", 0)),
            "fat_per_100g": float(result.get("fat_per_100g", 0)),
            "carbs_per_100g": float(result.get("carbs_per_100g", 0)),
            "estimated_grams": int(result.get("estimated_grams", 100)),
            "confidence": str(result.get("confidence", "средняя"))
        }
        
    except json.JSONDecodeError as e:
        return {"error": f"Не удалось распарсить JSON: {e}", "raw_response": raw[:200]}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def calculate_nutrition(data: dict) -> dict:
    """Рассчитывает КБЖУ для порции."""
    g = data.get("estimated_grams", 100)
    mult = g / 100.0
    return {
        "calories": round(data["calories_per_100g"] * mult),
        "protein": round(data["protein_per_100g"] * mult, 2),
        "fat": round(data["fat_per_100g"] * mult, 2),
        "carbs": round(data["carbs_per_100g"] * mult, 2),
        "grams": g
    }


def print_result(result: dict):
    """Красивый вывод результата."""
    print("\n" + "=" * 50)
    
    if "error" in result:
        print(f"❌ Ошибка: {result['error']}")
        if "raw_response" in result:
            print(f"📄 Сырой ответ: {result['raw_response']}")
    else:
        print(f"✅ Распознано: {result['food_name']}")
        print(f"   Уверенность: {result['confidence']}")
        print(f"   Примерный вес: {result['estimated_grams']} г")
        print()
        print("📊 На 100 г:")
        print(f"   🔥 Калории: {result['calories_per_100g']} ккал")
        print(f"   🥩 Белки:   {result['protein_per_100g']} г")
        print(f"   🧈 Жиры:    {result['fat_per_100g']} г")
        print(f"   🍚 Углеводы: {result['carbs_per_100g']} г")
        print()
        # Расчёт для порции
        portion = calculate_nutrition(result)
        print(f"🍽️ Для порции {portion['grams']} г:")
        print(f"   🔥 {portion['calories']} ккал | Б:{portion['protein']} Ж:{portion['fat']} У:{portion['carbs']}")
    
    print("=" * 50 + "\n")


async def main():
    # Загрузка переменных окружения
    env = load_env_file(Path(__file__).parent / ".env")
    api_key = env.get("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ Ошибка: GEMINI_API_KEY не найден в .env")
        print("💡 Добавьте строку в backend/.env:")
        print("   GEMINI_API_KEY=AIzaSy...")
        sys.exit(1)
    
    # Аргументы командной строки
    if len(sys.argv) < 2:
        print("🍽️  Распознавание еды через Google Gemini")
        print()
        print("Использование:")
        print(f"   python {sys.argv[0]} path/to/photo.jpg")
        print()
        print("Пример:")
        print(f"   python {sys.argv[0]} ../photos/lunch.jpg")
        sys.exit(0)
    
    image_path = sys.argv[1]
    
    print(f"🔑 Ключ API: {'✅ задан' if api_key else '❌ нет'}")
    print()
    
    # Распознавание
    result = await recognize_food(image_path, api_key)
    
    # Вывод
    print_result(result)


if __name__ == "__main__":
    asyncio.run(main())