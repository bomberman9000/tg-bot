
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from src.bot.states import Onboarding
from src.bot.keyboards import role_kb, contact_request_kb, main_menu
from src.core.database import async_session
from src.core.models import User, UserProfile, UserRole

router = Router()

ROLE_MAP = {
    "customer": UserRole.CUSTOMER,
    "carrier": UserRole.CARRIER,
    "forwarder": UserRole.FORWARDER,
}

ROLE_LABELS = {
    UserRole.CUSTOMER: "заказчик",
    UserRole.CARRIER: "перевозчик",
    UserRole.FORWARDER: "экспедитор",
}

async def get_profile(session, user_id: int) -> UserProfile | None:
    result = await session.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    return result.scalar_one_or_none()

async def ensure_profile(session, user_id: int) -> UserProfile:
    profile = await get_profile(session, user_id)
    if profile:
        return profile
    profile = UserProfile(user_id=user_id)
    session.add(profile)
    await session.commit()
    return profile

async def needs_onboarding(user_id: int) -> bool:
    async with async_session() as session:
        user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        profile = await get_profile(session, user_id)

    if not user:
        return True
    if not user.phone:
        return True
    if not profile:
        return True
    if not profile.role:
        return True
    if not profile.inn:
        return True
    if not user.company:
        return True
    return False

async def start_onboarding(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Добро пожаловать! Чтобы начать, выберите роль:",
        reply_markup=role_kb(),
    )
    await state.set_state(Onboarding.role)

@router.callback_query(Onboarding.role, F.data.startswith("role_"))
async def onboarding_role(cb: CallbackQuery, state: FSMContext):
    role_key = cb.data.replace("role_", "")
    role = ROLE_MAP.get(role_key)

    if not role:
        await cb.answer("❌ Неизвестная роль", show_alert=True)
        return

    async with async_session() as session:
        user = (await session.execute(select(User).where(User.id == cb.from_user.id))).scalar_one_or_none()
        profile = await ensure_profile(session, cb.from_user.id)
        profile.role = role
        if user:
            user.is_carrier = role == UserRole.CARRIER
        await session.commit()

    await state.update_data(role=role.value)
    await cb.message.answer(
        "📲 Поделись номером телефона через кнопку ниже.",
        reply_markup=contact_request_kb(),
    )
    await state.set_state(Onboarding.contact)
    await cb.answer()

@router.message(Onboarding.contact, F.contact)
async def onboarding_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number

    async with async_session() as session:
        user = (await session.execute(select(User).where(User.id == message.from_user.id))).scalar_one_or_none()
        profile = await ensure_profile(session, message.from_user.id)
        if user:
            user.phone = phone
        await session.commit()

    await message.answer("✅ Телефон сохранён.", reply_markup=ReplyKeyboardRemove())

    await message.answer("🧾 Укажи ИНН (10 или 12 цифр):")

    await state.set_state(Onboarding.inn)

@router.message(Onboarding.inn)
async def onboarding_inn(message: Message, state: FSMContext):
    inn = message.text.strip()
    if not inn.isdigit() or len(inn) not in (10, 12):
        await message.answer("❌ ИНН должен содержать 10 или 12 цифр")
        return

    async with async_session() as session:
        profile = await ensure_profile(session, message.from_user.id)
        profile.inn = inn
        await session.commit()

    await message.answer("🏢 Введи название компании (ООО/ИП):")
    await state.set_state(Onboarding.company)

@router.message(Onboarding.company)
async def onboarding_company(message: Message, state: FSMContext):
    company = message.text.strip()
    if not company:
        await message.answer("❌ Введи название компании")
        return

    async with async_session() as session:
        user = (await session.execute(select(User).where(User.id == message.from_user.id))).scalar_one_or_none()
        profile = await ensure_profile(session, message.from_user.id)
        if user:
            user.company = company
        await session.commit()

    await state.clear()
    await message.answer("✅ Регистрация завершена!", reply_markup=main_menu())
