from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from src.bot.states import CargoForm
from src.bot.keyboards import confirm_kb, cargo_actions, cargos_menu, back_menu, skip_kb, main_menu
from src.core.database import async_session
from src.core.models import Cargo, CargoStatus, CargoResponse, User
from src.core.logger import logger

router = Router()

@router.callback_query(F.data == "cargos")
async def cargos_menu_handler(cb: CallbackQuery):
    try:
        await cb.message.edit_text("🚛 <b>Грузы:</b>", reply_markup=cargos_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.callback_query(F.data == "menu")
async def back_to_menu(cb: CallbackQuery):
    try:
        await cb.message.edit_text(f"👋 <b>{cb.from_user.full_name}</b>, выбери:", reply_markup=main_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.callback_query(F.data == "all_cargos")
async def all_cargos(cb: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Cargo)
            .where(Cargo.status == CargoStatus.NEW)
            .order_by(Cargo.created_at.desc())
            .limit(10)
        )
        cargos = result.scalars().all()
    
    if not cargos:
        try:
            await cb.message.edit_text("📭 Нет активных грузов", reply_markup=cargos_menu())
        except TelegramBadRequest:
            pass
        await cb.answer()
        return
    
    text = "📋 <b>Активные грузы:</b>\n\n"
    for c in cargos:
        text += f"🔹 <b>{c.from_city} → {c.to_city}</b>\n"
        text += f"   {c.cargo_type}, {c.weight}т, {c.price}₽\n"
        text += f"   /cargo_{c.id}\n\n"
    
    try:
        await cb.message.edit_text(text, reply_markup=cargos_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.callback_query(F.data == "my_cargos")
async def my_cargos(cb: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Cargo)
            .where(Cargo.owner_id == cb.from_user.id)
            .order_by(Cargo.created_at.desc())
            .limit(10)
        )
        cargos = result.scalars().all()
    
    if not cargos:
        try:
            await cb.message.edit_text("📭 У тебя нет грузов", reply_markup=cargos_menu())
        except TelegramBadRequest:
            pass
        await cb.answer()
        return
    
    text = "📦 <b>Мои грузы:</b>\n\n"
    for c in cargos:
        status = "🟢" if c.status == CargoStatus.NEW else "🟡" if c.status == CargoStatus.IN_PROGRESS else "⚪"
        text += f"{status} <b>{c.from_city} → {c.to_city}</b>\n"
        text += f"   {c.weight}т, {c.price}₽ — /cargo_{c.id}\n\n"
    
    try:
        await cb.message.edit_text(text, reply_markup=cargos_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.message(F.text.startswith("/cargo_"))
async def view_cargo(message: Message):
    try:
        cargo_id = int(message.text.split("_")[1])
    except:
        return
    
    async with async_session() as session:
        result = await session.execute(select(Cargo).where(Cargo.id == cargo_id))
        cargo = result.scalar_one_or_none()
    
    if not cargo:
        await message.answer("❌ Груз не найден")
        return
    
    is_owner = cargo.owner_id == message.from_user.id
    
    text = f"📦 <b>Груз #{cargo.id}</b>\n\n"
    text += f"🛣 <b>{cargo.from_city} → {cargo.to_city}</b>\n"
    text += f"📦 {cargo.cargo_type}\n"
    text += f"⚖️ {cargo.weight} т\n"
    text += f"💰 {cargo.price} ₽\n"
    text += f"📅 {cargo.load_date.strftime('%d.%m.%Y')}\n"
    if cargo.comment:
        text += f"💬 {cargo.comment}\n"
    text += f"\nСтатус: {cargo.status.value}"
    
    await message.answer(text, reply_markup=cargo_actions(cargo.id, is_owner))

# === Создание груза ===
@router.callback_query(F.data == "add_cargo")
async def start_add_cargo(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("🏙 <b>Откуда:</b>\n\nВведи город отправления:")
    await state.set_state(CargoForm.from_city)
    await cb.answer()

@router.message(CargoForm.from_city)
async def cargo_from(message: Message, state: FSMContext):
    await state.update_data(from_city=message.text)
    await message.answer("🏙 <b>Куда:</b>\n\nВведи город назначения:")
    await state.set_state(CargoForm.to_city)

@router.message(CargoForm.to_city)
async def cargo_to(message: Message, state: FSMContext):
    await state.update_data(to_city=message.text)
    await message.answer("📦 <b>Тип груза:</b>\n\nНапример: Стройматериалы, Продукты, Техника")
    await state.set_state(CargoForm.cargo_type)

@router.message(CargoForm.cargo_type)
async def cargo_type(message: Message, state: FSMContext):
    await state.update_data(cargo_type=message.text)
    await message.answer("⚖️ <b>Вес (тонн):</b>\n\nНапример: 5 или 10.5")
    await state.set_state(CargoForm.weight)

@router.message(CargoForm.weight)
async def cargo_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", "."))
    except:
        await message.answer("❌ Введи число")
        return
    await state.update_data(weight=weight)
    await message.answer("💰 <b>Цена (₽):</b>\n\nСколько платишь за перевозку:")
    await state.set_state(CargoForm.price)

@router.message(CargoForm.price)
async def cargo_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.replace(" ", ""))
    except:
        await message.answer("❌ Введи число")
        return
    await state.update_data(price=price)
    await message.answer("📅 <b>Дата загрузки:</b>\n\nФормат: 25.01.2026")
    await state.set_state(CargoForm.load_date)

@router.message(CargoForm.load_date)
async def cargo_date(message: Message, state: FSMContext):
    try:
        load_date = datetime.strptime(message.text, "%d.%m.%Y")
    except:
        await message.answer("❌ Формат: 25.01.2026")
        return
    await state.update_data(load_date=load_date)
    await message.answer("💬 <b>Комментарий:</b>\n\nДоп. информация (или нажми пропустить)", reply_markup=skip_kb())
    await state.set_state(CargoForm.comment)

@router.message(CargoForm.comment)
async def cargo_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await show_cargo_confirm(message, state)

@router.callback_query(CargoForm.comment, F.data == "skip")
async def cargo_skip_comment(cb: CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    await show_cargo_confirm(cb.message, state)
    await cb.answer()

async def show_cargo_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    text = f"📦 <b>Подтверди груз:</b>\n\n"
    text += f"🛣 {data['from_city']} → {data['to_city']}\n"
    text += f"📦 {data['cargo_type']}\n"
    text += f"⚖️ {data['weight']} т\n"
    text += f"💰 {data['price']} ₽\n"
    text += f"📅 {data['load_date'].strftime('%d.%m.%Y')}\n"
    if data.get('comment'):
        text += f"💬 {data['comment']}\n"
    await message.answer(text, reply_markup=confirm_kb())
    await state.set_state(CargoForm.confirm)

@router.callback_query(CargoForm.confirm, F.data == "yes")
async def cargo_confirm_yes(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    async with async_session() as session:
        cargo = Cargo(
            owner_id=cb.from_user.id,
            from_city=data['from_city'],
            to_city=data['to_city'],
            cargo_type=data['cargo_type'],
            weight=data['weight'],
            price=data['price'],
            load_date=data['load_date'],
            comment=data.get('comment')
        )
        session.add(cargo)
        await session.commit()
        cargo_id = cargo.id
    
    logger.info(f"Cargo {cargo_id} created by {cb.from_user.id}")
    await cb.message.edit_text(f"✅ Груз #{cargo_id} создан!", reply_markup=main_menu())
    await state.clear()
    await cb.answer()

@router.callback_query(CargoForm.confirm, F.data == "no")
async def cargo_confirm_no(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("❌ Отменено", reply_markup=main_menu())
    await state.clear()
    await cb.answer()

# === Отклик на груз ===
@router.callback_query(F.data.startswith("respond_"))
async def respond_cargo(cb: CallbackQuery):
    cargo_id = int(cb.data.split("_")[1])
    
    async with async_session() as session:
        # Проверяем что не свой груз
        result = await session.execute(select(Cargo).where(Cargo.id == cargo_id))
        cargo = result.scalar_one_or_none()
        
        if not cargo:
            await cb.answer("❌ Груз не найден", show_alert=True)
            return
        
        if cargo.owner_id == cb.from_user.id:
            await cb.answer("❌ Это твой груз", show_alert=True)
            return
        
        # Проверяем нет ли уже отклика
        existing = await session.execute(
            select(CargoResponse)
            .where(CargoResponse.cargo_id == cargo_id)
            .where(CargoResponse.carrier_id == cb.from_user.id)
        )
        if existing.scalar_one_or_none():
            await cb.answer("⚠️ Ты уже откликнулся", show_alert=True)
            return
        
        # Создаем отклик
        response = CargoResponse(cargo_id=cargo_id, carrier_id=cb.from_user.id)
        session.add(response)
        await session.commit()
    
    logger.info(f"Response to cargo {cargo_id} from {cb.from_user.id}")
    await cb.answer("✅ Отклик отправлен!", show_alert=True)
