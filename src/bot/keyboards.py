from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, or_, and_
from src.bot.states import SearchCargo, SubscribeRoute
from src.bot.keyboards import cargos_menu, subscriptions_menu, back_menu, skip_kb, main_menu
from src.core.database import async_session
from src.core.models import Cargo, CargoStatus, RouteSubscription
from src.core.logger import logger

router = Router()

# === Поиск грузов ===
@router.callback_query(F.data == "search_cargo")
async def start_search(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("🔍 <b>Поиск грузов</b>\n\nОткуда? (или пропусти)", reply_markup=skip_kb())
    await state.set_state(SearchCargo.from_city)
    await cb.answer()

@router.message(SearchCargo.from_city)
async def search_from(message: Message, state: FSMContext):
    await state.update_data(from_city=message.text)
    await message.answer("Куда? (или пропусти)", reply_markup=skip_kb())
    await state.set_state(SearchCargo.to_city)

@router.callback_query(SearchCargo.from_city, F.data == "skip")
async def search_skip_from(cb: CallbackQuery, state: FSMContext):
    await state.update_data(from_city=None)
    await cb.message.edit_text("Куда? (или пропусти)", reply_markup=skip_kb())
    await state.set_state(SearchCargo.to_city)
    await cb.answer()

@router.message(SearchCargo.to_city)
async def search_to(message: Message, state: FSMContext):
    await state.update_data(to_city=message.text)
    await do_search(message, state)

@router.callback_query(SearchCargo.to_city, F.data == "skip")
async def search_skip_to(cb: CallbackQuery, state: FSMContext):
    await state.update_data(to_city=None)
    await do_search(cb.message, state)
    await cb.answer()

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
        
        result = await session.execute(query.order_by(Cargo.created_at.desc()).limit(10))
        cargos = result.scalars().all()
    
    await state.clear()
    
    if not cargos:
        await message.answer("📭 Грузов не найдено", reply_markup=cargos_menu())
        return
    
    text = f"🔍 <b>Найдено ({len(cargos)}):</b>\n\n"
    for c in cargos:
        text += f"🔹 <b>{c.from_city} → {c.to_city}</b>\n"
        text += f"   {c.cargo_type}, {c.weight}т, {c.price}₽\n"
        text += f"   /cargo_{c.id}\n\n"
    
    await message.answer(text, reply_markup=cargos_menu())

# === Подписки ===
@router.callback_query(F.data == "subscriptions")
async def subscriptions_handler(cb: CallbackQuery):
    try:
        await cb.message.edit_text("🔔 <b>Подписки на маршруты</b>\n\nПолучай уведомления о новых грузах!", reply_markup=subscriptions_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.callback_query(F.data == "add_subscription")
async def add_subscription(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("🔔 <b>Новая подписка</b>\n\nОткуда? (или пропусти для любого)", reply_markup=skip_kb())
    await state.set_state(SubscribeRoute.from_city)
    await cb.answer()

@router.message(SubscribeRoute.from_city)
async def sub_from(message: Message, state: FSMContext):
    await state.update_data(from_city=message.text)
    await message.answer("Куда? (или пропусти для любого)", reply_markup=skip_kb())
    await state.set_state(SubscribeRoute.to_city)

@router.callback_query(SubscribeRoute.from_city, F.data == "skip")
async def sub_skip_from(cb: CallbackQuery, state: FSMContext):
    await state.update_data(from_city=None)
    await cb.message.edit_text("Куда? (или пропусти для любого)", reply_markup=skip_kb())
    await state.set_state(SubscribeRoute.to_city)
    await cb.answer()

@router.message(SubscribeRoute.to_city)
async def sub_to(message: Message, state: FSMContext):
    await state.update_data(to_city=message.text)
    await save_subscription(message, state)

@router.callback_query(SubscribeRoute.to_city, F.data == "skip")
async def sub_skip_to(cb: CallbackQuery, state: FSMContext):
    await state.update_data(to_city=None)
    await save_subscription(cb.message, state)
    await cb.answer()

async def save_subscription(message: Message, state: FSMContext):
    data = await state.get_data()
    
    async with async_session() as session:
        sub = RouteSubscription(
            user_id=message.chat.id,
            from_city=data.get('from_city'),
            to_city=data.get('to_city')
        )
        session.add(sub)
        await session.commit()
    
    from_text = data.get('from_city') or 'любой'
    to_text = data.get('to_city') or 'любой'
    
    await state.clear()
    await message.answer(f"✅ Подписка добавлена!\n\n{from_text} → {to_text}", reply_markup=subscriptions_menu())
    logger.info(f"Subscription added for {message.chat.id}: {from_text} -> {to_text}")

@router.callback_query(F.data == "my_subscriptions")
async def my_subscriptions(cb: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(RouteSubscription)
            .where(RouteSubscription.user_id == cb.from_user.id)
            .where(RouteSubscription.is_active == True)
        )
        subs = result.scalars().all()
    
    if not subs:
        try:
            await cb.message.edit_text("📭 Нет активных подписок", reply_markup=subscriptions_menu())
        except TelegramBadRequest:
            pass
        await cb.answer()
        return
    
    text = "🔔 <b>Мои подписки:</b>\n\n"
    for s in subs:
        from_text = s.from_city or 'любой'
        to_text = s.to_city or 'любой'
        text += f"• {from_text} → {to_text}\n"
        text += f"  /unsub_{s.id}\n\n"
    
    try:
        await cb.message.edit_text(text, reply_markup=subscriptions_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.message(F.text.startswith("/unsub_"))
async def unsubscribe(message: Message):
    try:
        sub_id = int(message.text.split("_")[1])
    except:
        return
    
    async with async_session() as session:
        result = await session.execute(
            select(RouteSubscription)
            .where(RouteSubscription.id == sub_id)
            .where(RouteSubscription.user_id == message.from_user.id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.is_active = False
            await session.commit()
            await message.answer("✅ Подписка удалена", reply_markup=subscriptions_menu())
        else:
            await message.answer("❌ Подписка не найдена")
