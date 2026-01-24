from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, func
from src.bot.states import ProfileEdit
from src.bot.keyboards import main_menu, skip_kb, profile_menu
from src.bot.utils import cargo_deeplink
from src.core.database import async_session
from src.core.models import User, Cargo, CargoStatus, Rating
from src.core.logger import logger

router = Router()

@router.callback_query(F.data == "profile")
async def show_profile(cb: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == cb.from_user.id))
        user = result.scalar_one_or_none()
        
        if not user:
            await cb.answer("❌ Профиль не найден", show_alert=True)
            return
        
        avg_rating = await session.scalar(
            select(func.avg(Rating.score)).where(Rating.to_user_id == cb.from_user.id)
        )
        rating_count = await session.scalar(
            select(func.count()).select_from(Rating).where(Rating.to_user_id == cb.from_user.id)
        )
        
        cargos_count = await session.scalar(
            select(func.count()).select_from(Cargo).where(Cargo.owner_id == cb.from_user.id)
        )
        completed = await session.scalar(
            select(func.count()).select_from(Cargo)
            .where(Cargo.owner_id == cb.from_user.id)
            .where(Cargo.status == CargoStatus.COMPLETED)
        )
    
    stars = "⭐" * round(avg_rating) if avg_rating else "нет оценок"
    
    text = f"👤 <b>Мой профиль</b>\n\n"
    text += f"🆔 <code>{user.id}</code>\n"
    text += f"📝 {user.full_name}\n"
    if user.username:
        text += f"📱 @{user.username}\n"
    text += f"📞 {user.phone or 'не указан'}\n"
    text += f"🏢 {user.company or 'не указана'}\n\n"
    text += f"⭐ Рейтинг: {stars} ({rating_count})\n"
    text += f"📦 Грузов: {cargos_count} (завершено: {completed})\n"
    text += f"📅 С нами с: {user.created_at.strftime('%d.%m.%Y')}"
    
    try:
        await cb.message.edit_text(text, reply_markup=profile_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.callback_query(F.data == "edit_phone")
async def edit_phone(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("📞 Введи номер телефона:")
    await state.set_state(ProfileEdit.phone)
    await cb.answer()

@router.message(ProfileEdit.phone)
async def save_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == message.from_user.id))
        user = result.scalar_one_or_none()
        if user:
            user.phone = phone
            await session.commit()
    
    await state.clear()
    await message.answer(f"✅ Телефон сохранён: {phone}", reply_markup=main_menu())
    logger.info(f"User {message.from_user.id} updated phone: {phone}")

@router.callback_query(F.data == "edit_company")
async def edit_company(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("🏢 Введи название компании:")
    await state.set_state(ProfileEdit.company)
    await cb.answer()

@router.message(ProfileEdit.company)
async def save_company(message: Message, state: FSMContext):
    company = message.text.strip()
    
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == message.from_user.id))
        user = result.scalar_one_or_none()
        if user:
            user.company = company
            await session.commit()
    
    await state.clear()
    await message.answer(f"✅ Компания: {company}", reply_markup=main_menu())
    logger.info(f"User {message.from_user.id} updated company: {company}")

@router.callback_query(F.data == "history")
async def show_history(cb: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Cargo)
            .where(
                (Cargo.owner_id == cb.from_user.id) | (Cargo.carrier_id == cb.from_user.id)
            )
            .where(Cargo.status == CargoStatus.COMPLETED)
            .order_by(Cargo.created_at.desc())
            .limit(10)
        )
        cargos = result.scalars().all()
    
    if not cargos:
        try:
            await cb.message.edit_text("📜 История пуста", reply_markup=profile_menu())
        except TelegramBadRequest:
            pass
        await cb.answer()
        return
    
    text = "📜 <b>История перевозок:</b>\n\n"
    for c in cargos:
        role = "📦" if c.owner_id == cb.from_user.id else "🚛"
        link = cargo_deeplink(c.id)
        text += f"{role} {c.from_city} → {c.to_city}\n"
        text += f"   {c.weight}т, {c.price}₽ — {link}\n\n"
    
    try:
        await cb.message.edit_text(text, reply_markup=profile_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()
