from groq import Groq
from src.core.config import settings
from src.core.logger import logger
import json
import math
import re

client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None

CITY_ALIASES = {
    "мск": "Москва", "москва": "Москва",
    "спб": "Санкт-Петербург", "питер": "Санкт-Петербург", "петербург": "Санкт-Петербург",
    "нск": "Новосибирск", "новосиб": "Новосибирск",
    "екб": "Екатеринбург", "ёбург": "Екатеринбург",
    "казань": "Казань", "кзн": "Казань",
    "нн": "Нижний Новгород", "нижний": "Нижний Новгород",
    "самара": "Самара", "самар": "Самара",
    "ростов": "Ростов-на-Дону", "рнд": "Ростов-на-Дону",
    "уфа": "Уфа",
    "красноярск": "Красноярск", "крск": "Красноярск",
    "воронеж": "Воронеж", "врн": "Воронеж",
    "пермь": "Пермь",
    "волгоград": "Волгоград",
    "краснодар": "Краснодар", "крд": "Краснодар",
    "челябинск": "Челябинск", "челяба": "Челябинск",
    "омск": "Омск",
    "тюмень": "Тюмень",
}

async def parse_city(text: str) -> str | None:
    """Распознать город из текста"""
    text_lower = text.lower().strip()

    # Сначала проверяем алиасы
    if text_lower in CITY_ALIASES:
        return CITY_ALIASES[text_lower]

    # Проверяем частичное совпадение
    for alias, city in CITY_ALIASES.items():
        if alias in text_lower or text_lower in alias:
            return city

    # Если не нашли — спрашиваем AI
    if not client:
        return text.title()

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "system",
                "content": "Ты помощник для распознавания городов России. Пользователь вводит название города, возможно с опечаткой или сокращением. Верни только название города с большой буквы. Если не можешь распознать — верни исходный текст."
            }, {
                "role": "user",
                "content": f"Распознай город: {text}"
            }],
            max_tokens=50,
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        logger.info(f"AI parsed city: {text} -> {result}")
        return result
    except Exception as e:
        logger.error(f"AI city parse error: {e}")
        return text.title()

async def parse_cargo_request(text: str) -> dict | None:
    """Парсит запрос на груз из естественного языка"""
    if not client:
        return None

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "system",
                "content": """Ты помощник для парсинга заявок на грузоперевозки. 
Извлеки из текста: откуда, куда, вес (тонны), цену (рубли), тип груза.
Верни JSON: {\"from_city\": \"...\", \"to_city\": \"...\", \"weight\": число, \"price\": число, \"cargo_type\": \"...\"}
Если чего-то нет — не включай в JSON. Города пиши полностью с большой буквы."""
            }, {
                "role": "user",
                "content": text
            }],
            max_tokens=200,
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        # Извлекаем JSON
        if "{" in result and "}" in result:
            json_str = result[result.find("{"):result.rfind("}")+1]
            data = json.loads(json_str)
            logger.info(f"AI parsed cargo: {text} -> {data}")
            return data
    except Exception as e:
        logger.error(f"AI cargo parse error: {e}")
    return None

async def estimate_price(from_city: str, to_city: str, weight: float) -> int | None:
    """Оценка цены перевозки"""
    if not client:
        return None

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "system",
                "content": """Ты эксперт по грузоперевозкам в России. 
Оцени примерную стоимость перевозки груза.
Учитывай: расстояние между городами, вес груза.
Средняя ставка: 30-50 руб/км для фуры, минимум 5000 руб.
Верни только число в рублях, без пояснений."""
            }, {
                "role": "user",
                "content": f"Перевозка {weight} тонн из {from_city} в {to_city}"
            }],
            max_tokens=50,
            temperature=0.3
        )
        result = response.choices[0].message.content.strip()
        # Извлекаем число
        price = int(''.join(filter(str.isdigit, result)))
        logger.info(f"AI estimated price: {from_city}->{to_city}, {weight}t = {price}₽")
        return price
    except Exception as e:
        logger.error(f"AI price estimate error: {e}")
    return None

def _normalize_city_key(text: str) -> str:
    t = (text or "").strip().lower()
    if not t:
        return ""
    t = t.replace("ё", "е")
    t = t.replace("-", " ")
    t = re.sub(r"[^0-9a-zа-я\\s]", " ", t)
    t = re.sub(r"\\s+", " ", t).strip()
    return t

CITY_COORDS: dict[str, tuple[float, float]] = {
    "москва": (55.7558, 37.6173),
    "санкт петербург": (59.9311, 30.3609),
    "новосибирск": (55.0084, 82.9357),
    "екатеринбург": (56.8389, 60.6057),
    "нижний новгород": (56.2965, 43.9361),
    "казань": (55.7961, 49.1064),
    "самара": (53.1959, 50.1002),
    "омск": (54.9885, 73.3242),
    "ростов на дону": (47.2357, 39.7015),
    "уфа": (54.7388, 55.9721),
    "красноярск": (56.0097, 92.7917),
    "пермь": (58.0105, 56.2502),
    "воронеж": (51.6608, 39.2003),
    "волгоград": (48.7080, 44.5133),
    "краснодар": (45.0355, 38.9753),
    "челябинск": (55.1644, 61.4368),
    "тюмень": (57.1530, 65.5343),
    "симферополь": (44.9521, 34.1024),
    "мурманск": (68.9585, 33.0827),
    "ставрополь": (45.0428, 41.9734),
    "набережные челны": (55.7436, 52.3958),
}

def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))

def estimate_price_local(from_city: str, to_city: str, weight: float) -> dict | None:
    """Локальная оценка цены по расстоянию (если известны координаты городов)"""
    a = CITY_COORDS.get(_normalize_city_key(from_city))
    b = CITY_COORDS.get(_normalize_city_key(to_city))
    if not a or not b:
        return None

    distance = _haversine_km(a, b)
    distance_km = max(1, int(distance))

    rate_per_km = 35 + min(weight, 20) * 0.5
    rate_per_km = max(30, min(50, rate_per_km))

    min_price = int(distance_km * 30)
    max_price = int(distance_km * 50)
    price = int(distance_km * rate_per_km)

    return {
        "price": price,
        "distance": distance_km,
        "rate_per_km": int(rate_per_km),
        "min_price": min_price,
        "max_price": max_price,
    }

async def get_market_price(from_city: str, to_city: str, weight: float, cargo_type: str = "тент") -> dict | None:
    """Получить рыночную цену с учётом веса"""
    from src.core.database import async_session
    from src.core.models import MarketPrice
    from sqlalchemy import select

    cargo_type_key = (cargo_type or "тент").strip()

    async with async_session() as session:
        price_data = await session.scalar(
            select(MarketPrice).where(
                MarketPrice.from_city == from_city,
                MarketPrice.to_city == to_city,
                MarketPrice.cargo_type.ilike(f"%{cargo_type_key[:3]}%"),
            )
        )

        if not price_data:
            price_data = await session.scalar(
                select(MarketPrice).where(
                    MarketPrice.from_city == to_city,
                    MarketPrice.to_city == from_city,
                    MarketPrice.cargo_type.ilike(f"%{cargo_type_key[:3]}%"),
                )
            )

        if not price_data:
            return None

        base_price = price_data.price
        base_weight = price_data.weight or 20.0

        if weight >= base_weight:
            adjusted_price = base_price
        elif weight >= 10:
            adjusted_price = int(base_price * (0.6 + 0.02 * weight))
        elif weight >= 5:
            adjusted_price = int(base_price * (0.4 + 0.02 * weight))
        else:
            adjusted_price = int(base_price * 0.4)

        return {
            "market_price": base_price,
            "adjusted_price": adjusted_price,
            "base_weight": base_weight,
            "your_weight": weight,
            "source": price_data.source,
            "updated": price_data.updated_at.strftime("%d.%m.%Y"),
            "cargo_type": price_data.cargo_type,
        }

async def estimate_price_smart(from_city: str, to_city: str, weight: float, cargo_type: str = "тент") -> dict:
    """Умная оценка цены: сначала рынок, потом расчёт"""
    market = await get_market_price(from_city, to_city, weight, cargo_type)
    if market:
        return {
            "price": market["adjusted_price"],
            "source": "market",
            "market_price_20t": market["market_price"],
            "details": (
                f"📊 Рыночная цена ({market['source']})\\n"
                f"• За 20т: {market['market_price']:,} ₽\\n"
                f"• За {weight}т: {market['adjusted_price']:,} ₽\\n"
                f"• Данные от {market['updated']}"
            ),
        }

    local = estimate_price_local(from_city, to_city, weight)
    if local:
        return {
            "price": local["price"],
            "source": "calculated",
            "distance": local["distance"],
            "details": (
                "📐 Расчётная цена\\n"
                f"• Расстояние: ~{local['distance']} км\\n"
                f"• Ставка: ~{local['rate_per_km']} ₽/км\\n"
                f"• Диапазон: {local['min_price']:,} — {local['max_price']:,} ₽"
            ),
        }

    return {
        "price": None,
        "source": "unknown",
        "details": "❓ Недостаточно данных для оценки",
    }

async def chat_response(user_message: str, context: str = "") -> str:
    """Ответ на вопрос пользователя"""
    if not client:
        return "AI временно недоступен"

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "system",
                "content": f"""Ты помощник в боте грузоперевозок. Отвечай кратко и по делу на русском языке.
{context}
Если вопрос не по теме — вежливо направь к функциям бота."""
            }, {
                "role": "user",
                "content": user_message
            }],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        return "Произошла ошибка. Попробуйте позже."
