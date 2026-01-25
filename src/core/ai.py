from groq import Groq
from src.core.config import settings
from src.core.logger import logger
import json

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
