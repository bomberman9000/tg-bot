from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, or_
from src.bot.states import SearchCargo, SubscribeRoute
from src.bot.keyboards import cargos_menu, subscriptions_menu, city_kb
from src.bot.utils import cargo_deeplink
from src.bot.utils.cities import city_suggest
from src.core.database import async_session
from src.core.models import Cargo, CargoStatus, RouteSubscription
from src.core.logger import logger

router = Router()

CANCEL_HINT = "\n\n❌ Отмена: /cancel"

@router.callback_query(F.data == "search_cargo")
async def start_search(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        "🔍 Найдём груз\n\n"
        "Откуда? Начни вводить город (например: «самар», «мос», «спб»)"
        + CANCEL_HINT,
        reply_markup=city_kb([], "from"),
    )
    await state.set_state(SearchCargo.from_city)
    await cb.answer()

@router.message(SearchCargo.from_city)
async def search_from(message: Message, state: FSMContext):
    suggestions = city_suggest(message.text)
    if not suggestions:
        await message.answer(
            "Я жду город отправления. Начни ввод: «мос», «самар», «спб»."
            + CANCEL_HINT,
            reply_markup=city_kb([], "from"),
        )
        return
    await message.answer(
        "Выбери город отправления:" + CANCEL_HINT,
        reply_markup=city_kb(suggestions, "from"),
    )

@router.message(SearchCargo.to_city)
async def search_to(message: Message, state: FSMContext):
    suggestions = city_suggest(message.text)
    if not suggestions:
        await message.answer(
            "Я жду город назначения. Начни ввод: «мос», «самар», «спб»."
            + CANCEL_HINT,
            reply_markup=city_kb([], "to"),
        )
        return
    await message.answer(
        "Выбери город назначения:" + CANCEL_HINT,
        reply_markup=city_kb(suggestions, "to"),
    )

@router.callback_query(SearchCargo.from_city, F.data.startswith("city:from:"))
async def search_from_select(cb: CallbackQuery, state: FSMContext):
    _, _, city = cb.data.split(":", 2)
    await state.update_data(from_city=city)
    await state.set_state(SearchCargo.to_city)
    await cb.message.edit_text(
        f"✅ Выбрано: {city}\n\n"
        "Куда доставить? Начни вводить город (например: «самар», «мос», «спб»)"
        + CANCEL_HINT,
        reply_markup=city_kb([], "to"),
    )
    await cb.answer()

@router.callback_query(SearchCargo.to_city, F.data.startswith("city:to:"))
async def search_to_select(cb: CallbackQuery, state: FSMContext):
    _, _, city = cb.data.split(":", 2)
    await state.update_data(to_city=city)
    await cb.message.edit_text(f"✅ Выбрано: {city}\n\nИщу грузы…")
    await cb.answer()
    await do_search(cb.message, state)

async def do_search(message: Message, state: FSMContext):
    data = await state.get_data()
    from_city = data.get('from_city')
    to_city = data.get('to_city')
    
    async with async_session() as session:
        query = select(Cargo).where(Cargo.status == CargoStatus.NEW)
        if from_city:
            query = query.where(Cargo.from_city.ilike(f"%{from_city}%"))
        if to_city:
            query = query.where(Cargo.to_city.ilike(f"%{to_city}%"))
        result = await session.execute(query.limit(10))
        cargos = result.scalars().all()
    
    await state.clear()
    
    if not cargos:
        await message.answer("📭 Ничего не нашли. Попробуй другие параметры.", reply_markup=cargos_menu())
        return
    
    text = f"🔍 Найдено ({len(cargos)}):\n\n"
    for c in cargos:
        link = cargo_deeplink(c.id)
        text += f"🔹 {c.from_city} → {c.to_city}\n   {c.weight}т, {c.price}₽ {link}\n\n"
    await message.answer(text, reply_markup=cargos_menu())

@router.callback_query(F.data == "subscriptions")
async def subscriptions_handler(cb: CallbackQuery):
    try:
        await cb.message.edit_text("🔔 Подписки на маршруты\n\nПолучай уведомления о новых грузах по своим маршрутам.", reply_markup=subscriptions_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.callback_query(F.data == "add_subscription")
async def add_subscription(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        "Откуда? Начни вводить город (например: «самар», «мос», «спб»)"
        + CANCEL_HINT,
        reply_markup=city_kb([], "from"),
    )
    await state.set_state(SubscribeRoute.from_city)
    await cb.answer()

@router.message(SubscribeRoute.from_city)
async def sub_from(message: Message, state: FSMContext):
    suggestions = city_suggest(message.text)
    if not suggestions:
        await message.answer(
            "Я жду город отправления. Начни ввод: «мос», «самар», «спб»."
            + CANCEL_HINT,
            reply_markup=city_kb([], "from"),
        )
        return
    await message.answer(
        "Выбери город отправления:" + CANCEL_HINT,
        reply_markup=city_kb(suggestions, "from"),
    )

@router.message(SubscribeRoute.to_city)
async def sub_to(message: Message, state: FSMContext):
    suggestions = city_suggest(message.text)
    if not suggestions:
        await message.answer(
            "Я жду город назначения. Начни ввод: «мос», «самар», «спб»."
            + CANCEL_HINT,
            reply_markup=city_kb([], "to"),
        )
        return
    await message.answer(
        "Выбери город назначения:" + CANCEL_HINT,
        reply_markup=city_kb(suggestions, "to"),
    )

@router.callback_query(SubscribeRoute.from_city, F.data.startswith("city:from:"))
async def sub_from_select(cb: CallbackQuery, state: FSMContext):
    _, _, city = cb.data.split(":", 2)
    await state.update_data(from_city=city)
    await state.set_state(SubscribeRoute.to_city)
    await cb.message.edit_text(
        f"✅ Выбрано: {city}\n\n"
        "Куда доставить? Начни вводить город (например: «самар», «мос», «спб»)"
        + CANCEL_HINT,
        reply_markup=city_kb([], "to"),
    )
    await cb.answer()

@router.callback_query(SubscribeRoute.to_city, F.data.startswith("city:to:"))
async def sub_to_select(cb: CallbackQuery, state: FSMContext):
    _, _, city = cb.data.split(":", 2)
    await state.update_data(to_city=city)
    await cb.message.edit_text(f"✅ Выбрано: {city}")
    await cb.answer()
    await save_subscription(cb.message, state)

async def save_subscription(message: Message, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        sub = RouteSubscription(user_id=message.chat.id, from_city=data.get('from_city'), to_city=data.get('to_city'))
        session.add(sub)
    await session.commit()
    await state.clear()
    await message.answer(
        f"✅ Подписка сохранена: {data.get('from_city')} → {data.get('to_city')}",
        reply_markup=subscriptions_menu()
    )

@router.callback_query(F.data == "my_subscriptions")
async def my_subscriptions(cb: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(RouteSubscription).where(RouteSubscription.user_id == cb.from_user.id).where(RouteSubscription.is_active == True))
        subs = result.scalars().all()
    if not subs:
        await cb.message.edit_text("📭 Нет активных подписок", reply_markup=subscriptions_menu())
        await cb.answer()
        return
    text = "🔔 Подписки:\n\n"
    for s in subs:
        text += f"• {s.from_city} → {s.to_city} /unsub_{s.id}\n"
    await cb.message.edit_text(text, reply_markup=subscriptions_menu())
    await cb.answer()

@router.message(F.text.startswith("/unsub_"))
async def unsubscribe(message: Message):
    try:
        sub_id = int(message.text.split("_")[1])
    except:
        return
    async with async_session() as session:
        result = await session.execute(select(RouteSubscription).where(RouteSubscription.id == sub_id).where(RouteSubscription.user_id == message.from_user.id))
        sub = result.scalar_one_or_none()
        if sub:
            sub.is_active = False
            await session.commit()
            await message.answer("✅ Удалено", reply_markup=subscriptions_menu())
