from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy import select
from src.bot.states import CargoSearch, CargoFilter
from src.bot.keyboards import main_menu
from src.core.database import async_session
from src.core.models import Cargo, CargoStatus, User, RouteSubscription
from src.core.logger import logger

router = Router()

def search_menu(has_filters: bool = False):
    b = InlineKeyboardBuilder()
    filter_text = "🔧 Фильтры ✓" if has_filters else "🔧 Фильтры"
    b.row(InlineKeyboardButton(text=filter_text, callback_data="filters"))
    b.row(InlineKeyboardButton(text="🔔 Подписаться", callback_data="subscribe_route"))
    b.row(InlineKeyboardButton(text="◀️ Меню", callback_data="menu"))
    return b.as_markup()

def filters_menu():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="⚖️ Вес от", callback_data="filter_weight_min"),
          InlineKeyboardButton(text="⚖️ Вес до", callback_data="filter_weight_max"))
    b.row(InlineKeyboardButton(text="💰 Цена от", callback_data="filter_price_min"),
          InlineKeyboardButton(text="💰 Цена до", callback_data="filter_price_max"))
    b.row(InlineKeyboardButton(text="🗑 Сбросить", callback_data="filter_reset"))
    b.row(InlineKeyboardButton(text="🔍 Искать", callback_data="do_search"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="search"))
    return b.as_markup()

@router.callback_query(F.data == "search")
async def start_search(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CargoSearch.from_city)
    data = await state.get_data()
    filters_text = ""
    if any(data.get(k) for k in ["weight_min", "weight_max", "price_min", "price_max"]):
        filters_text = "\n\n🔧 <i>Фильтры активны</i>"
    try:
        await cb.message.edit_text(f"🔍 <b>Поиск грузов</b>\n\nВведи город отправления:{filters_text}")
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.message(CargoSearch.from_city)
async def search_from_city(message: Message, state: FSMContext):
    await state.update_data(from_city=message.text.strip())
    await state.set_state(CargoSearch.to_city)
    await message.answer("📍 Введи город назначения (или /skip для любого):")

@router.message(CargoSearch.to_city)
async def search_to_city(message: Message, state: FSMContext):
    to_city = None if message.text == "/skip" else message.text.strip()
    await state.update_data(to_city=to_city)
    await state.set_state(None)
    await do_search_action(message, state, edit=False)

@router.callback_query(F.data == "filters")
async def show_filters(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = "🔧 <b>Фильтры поиска</b>\n\n"
    text += f"⚖️ Вес: {data.get('weight_min', '—')} — {data.get('weight_max', '—')} т\n"
    text += f"💰 Цена: {data.get('price_min', '—')} — {data.get('price_max', '—')} ₽"
    try:
        await cb.message.edit_text(text, reply_markup=filters_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.callback_query(F.data == "filter_weight_min")
async def filter_weight_min(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CargoFilter.weight_min)
    await cb.message.edit_text("⚖️ Введи минимальный вес (тонн):")
    await cb.answer()

@router.message(CargoFilter.weight_min)
async def save_weight_min(message: Message, state: FSMContext):
    try:
        val = float(message.text.replace(",", "."))
        await state.update_data(weight_min=val)
        await state.set_state(None)
        await message.answer(f"✅ Мин. вес: {val} т", reply_markup=main_menu())
    except ValueError:
        await message.answer("❌ Введи число")

@router.callback_query(F.data == "filter_weight_max")
async def filter_weight_max(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CargoFilter.weight_max)
    await cb.message.edit_text("⚖️ Введи максимальный вес (тонн):")
    await cb.answer()

@router.message(CargoFilter.weight_max)
async def save_weight_max(message: Message, state: FSMContext):
    try:
        val = float(message.text.replace(",", "."))
        await state.update_data(weight_max=val)
        await state.set_state(None)
        await message.answer(f"✅ Макс. вес: {val} т", reply_markup=main_menu())
    except ValueError:
        await message.answer("❌ Введи число")

@router.callback_query(F.data == "filter_price_min")
async def filter_price_min(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CargoFilter.price_min)
    await cb.message.edit_text("💰 Введи минимальную цену (₽):")
    await cb.answer()

@router.message(CargoFilter.price_min)
async def save_price_min(message: Message, state: FSMContext):
    try:
        val = int(message.text.replace(" ", "").replace("₽", ""))
        await state.update_data(price_min=val)
        await state.set_state(None)
        await message.answer(f"✅ Мин. цена: {val} ₽", reply_markup=main_menu())
    except ValueError:
        await message.answer("❌ Введи число")

@router.callback_query(F.data == "filter_price_max")
async def filter_price_max(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CargoFilter.price_max)
    await cb.message.edit_text("💰 Введи максимальную цену (₽):")
    await cb.answer()

@router.message(CargoFilter.price_max)
async def save_price_max(message: Message, state: FSMContext):
    try:
        val = int(message.text.replace(" ", "").replace("₽", ""))
        await state.update_data(price_max=val)
        await state.set_state(None)
        await message.answer(f"✅ Макс. цена: {val} ₽", reply_markup=main_menu())
    except ValueError:
        await message.answer("❌ Введи число")

@router.callback_query(F.data == "filter_reset")
async def filter_reset(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_data({"from_city": data.get("from_city"), "to_city": data.get("to_city")})
    await cb.answer("✅ Фильтры сброшены", show_alert=True)
    await show_filters(cb, state)

@router.callback_query(F.data == "do_search")
async def do_search_callback(cb: CallbackQuery, state: FSMContext):
    await do_search_action(cb.message, state, edit=True)
    await cb.answer()

async def do_search_action(message: Message, state: FSMContext, edit: bool = False):
    data = await state.get_data()
    from_city = data.get("from_city")
    to_city = data.get("to_city")
    weight_min = data.get("weight_min")
    weight_max = data.get("weight_max")
    price_min = data.get("price_min")
    price_max = data.get("price_max")
    
    async with async_session() as session:
        query = select(Cargo).where(Cargo.status == CargoStatus.NEW)
        if from_city:
            query = query.where(Cargo.from_city.ilike(f"%{from_city}%"))
        if to_city:
            query = query.where(Cargo.to_city.ilike(f"%{to_city}%"))
        if weight_min:
            query = query.where(Cargo.weight >= weight_min)
        if weight_max:
            query = query.where(Cargo.weight <= weight_max)
        if price_min:
            query = query.where(Cargo.price >= price_min)
        if price_max:
            query = query.where(Cargo.price <= price_max)
        query = query.order_by(Cargo.created_at.desc()).limit(20)
        result = await session.execute(query)
        cargos = result.scalars().all()
    
    has_filters = any([weight_min, weight_max, price_min, price_max])
    
    if not cargos:
        text = f"🔍 <b>{from_city or 'Все'}</b> → <b>{to_city or 'Все'}</b>\n\n"
        text += "❌ Грузов не найдено"
        if edit:
            try:
                await message.edit_text(text, reply_markup=search_menu(has_filters))
            except TelegramBadRequest:
                pass
        else:
            await message.answer(text, reply_markup=search_menu(has_filters))
        return
    
    text = f"🔍 <b>{from_city or 'Все'}</b> → <b>{to_city or 'Все'}</b>\n"
    if has_filters:
        text += "🔧 <i>Фильтры применены</i>\n"
    text += f"Найдено: {len(cargos)}\n\n"
    for c in cargos:
        text += f"📦 <b>{c.from_city}</b> → <b>{c.to_city}</b>\n"
        text += f"   ⚖️ {c.weight}т | 💰 {c.price}₽ | /cargo_{c.id}\n\n"
    
    if edit:
        try:
            await message.edit_text(text, reply_markup=search_menu(has_filters))
        except TelegramBadRequest:
            pass
    else:
        await message.answer(text, reply_markup=search_menu(has_filters))

@router.callback_query(F.data == "subscribe_route")
async def subscribe_route(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    from_city = data.get("from_city")
    if not from_city:
        await cb.answer("❌ Сначала выполни поиск", show_alert=True)
        return
    to_city = data.get("to_city")
    async with async_session() as session:
        existing = await session.execute(
            select(RouteSubscription).where(
                RouteSubscription.user_id == cb.from_user.id,
                RouteSubscription.from_city == from_city,
                RouteSubscription.to_city == to_city
            )
        )
        if existing.scalar_one_or_none():
            await cb.answer("⚠️ Уже подписан", show_alert=True)
            return
        sub = RouteSubscription(user_id=cb.from_user.id, from_city=from_city, to_city=to_city)
        session.add(sub)
        await session.commit()
    await cb.answer(f"✅ Подписка: {from_city} → {to_city or 'Все'}", show_alert=True)

@router.callback_query(F.data.startswith("respond_"))
async def respond_cargo(cb: CallbackQuery):
    cargo_id = int(cb.data.split("_")[1])
    async with async_session() as session:
        result = await session.execute(select(Cargo).where(Cargo.id == cargo_id))
        cargo = result.scalar_one_or_none()
        if not cargo:
            await cb.answer("❌ Груз не найден", show_alert=True)
            return
        if cargo.status != CargoStatus.NEW:
            await cb.answer("❌ Груз уже взят", show_alert=True)
            return
        if cargo.owner_id == cb.from_user.id:
            await cb.answer("❌ Это твой груз", show_alert=True)
            return
        carrier_result = await session.execute(select(User).where(User.id == cb.from_user.id))
        carrier = carrier_result.scalar_one_or_none()
        from src.bot.bot import bot
        try:
            carrier_info = f"@{carrier.username}" if carrier.username else carrier.full_name
            if carrier.phone:
                carrier_info += f" ({carrier.phone})"
            notify_kb = InlineKeyboardBuilder()
            notify_kb.row(
                InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{cargo_id}_{cb.from_user.id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{cargo_id}_{cb.from_user.id}")
            )
            await bot.send_message(
                cargo.owner_id,
                f"🚛 <b>Новый отклик!</b>\n\nГруз: {cargo.from_city} → {cargo.to_city}\nПеревозчик: {carrier_info}\n\n/cargo_{cargo_id}",
                reply_markup=notify_kb.as_markup()
            )
            await cb.answer("✅ Отклик отправлен", show_alert=True)
        except Exception as e:
            logger.error(f"Notify error: {e}")
            await cb.answer("⚠️ Отклик отправлен", show_alert=True)

@router.callback_query(F.data.startswith("accept_"))
async def accept_response(cb: CallbackQuery):
    parts = cb.data.split("_")
    cargo_id = int(parts[1])
    carrier_id = int(parts[2])
    async with async_session() as session:
        result = await session.execute(select(Cargo).where(Cargo.id == cargo_id))
        cargo = result.scalar_one_or_none()
        if not cargo or cargo.owner_id != cb.from_user.id:
            await cb.answer("❌ Ошибка", show_alert=True)
            return
        if cargo.status != CargoStatus.NEW:
            await cb.answer("❌ Груз уже в работе", show_alert=True)
            return
        cargo.carrier_id = carrier_id
        cargo.status = CargoStatus.IN_PROGRESS
        await session.commit()
        from src.bot.bot import bot
        try:
            await bot.send_message(
                carrier_id,
                f"✅ <b>Отклик принят!</b>\n\nГруз: {cargo.from_city} → {cargo.to_city}\n⚖️ {cargo.weight}т | 💰 {cargo.price}₽\n\n/cargo_{cargo_id}"
            )
        except Exception as e:
            logger.error(f"Notify error: {e}")
    await cb.answer("✅ Перевозчик назначен", show_alert=True)
    try:
        await cb.message.edit_text(cb.message.text + "\n\n✅ <b>Перевозчик назначен</b>", reply_markup=None)
    except TelegramBadRequest:
        pass

@router.callback_query(F.data.startswith("reject_"))
async def reject_response(cb: CallbackQuery):
    parts = cb.data.split("_")
    cargo_id = int(parts[1])
    carrier_id = int(parts[2])
    from src.bot.bot import bot
    try:
        await bot.send_message(carrier_id, f"❌ <b>Отклик отклонён</b>\n\n/cargo_{cargo_id}")
    except Exception as e:
        logger.error(f"Notify error: {e}")
    await cb.answer("❌ Отклонено", show_alert=True)
    try:
        await cb.message.edit_text(cb.message.text + "\n\n❌ <b>Отклонено</b>", reply_markup=None)
    except TelegramBadRequest:
        pass

@router.callback_query(F.data.startswith("contact_"))
async def contact_owner(cb: CallbackQuery):
    cargo_id = int(cb.data.split("_")[1])
    async with async_session() as session:
        result = await session.execute(select(Cargo).where(Cargo.id == cargo_id))
        cargo = result.scalar_one_or_none()
        if not cargo:
            await cb.answer("❌ Груз не найден", show_alert=True)
            return
        owner_result = await session.execute(select(User).where(User.id == cargo.owner_id))
        owner = owner_result.scalar_one_or_none()
    if owner:
        contact = f"@{owner.username}" if owner.username else owner.full_name
        if owner.phone:
            contact += f"\n📞 {owner.phone}"
        await cb.answer(f"📞 {contact}", show_alert=True)
    else:
        await cb.answer("❌ Контакт недоступен", show_alert=True)
