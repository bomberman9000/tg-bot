from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.types import ReplyKeyboardRemove
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from src.bot.keyboards import main_menu, role_kb, contact_request_kb, legal_type_kb
from src.bot.handlers.cargo import send_cargo_details
from src.core.database import async_session
from src.core.models import User, Reminder, UserProfile, UserRole
from src.bot.states import Onboarding

router = Router()

ROLE_MAP = {
    "customer": UserRole.CUSTOMER,
    "carrier": UserRole.CARRIER,
    "forwarder": UserRole.FORWARDER,
}

CANCEL_HINT = "\n\n❌ Отмена: /cancel"

async def upsert_text(obj, text: str, reply_markup=None, disable_web_page_preview=True):
    """
    Унифицирует вывод: если это CallbackQuery — редактируем его message.
    Если Message — пытаемся отредактировать последнее (сам Message) если возможно,
    иначе отправляем новое.
    """
    try:
        if isinstance(obj, CallbackQuery):
            return await obj.message.edit_text(
                text,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
            )
        return await obj.edit_text(
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
        )
    except (TelegramBadRequest, AttributeError):
        if isinstance(obj, CallbackQuery):
            return await obj.message.answer(
                text,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
            )
        return await obj.answer(
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
        )

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
    if profile.role in (UserRole.CUSTOMER, UserRole.FORWARDER):
        if not profile.inn or not user.company:
            return True
    if profile.role == UserRole.CARRIER:
        if profile.inn and not user.company:
            return True
    return False

async def start_onboarding(obj: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    await upsert_text(
        obj,
        "👋 Добро пожаловать! Чтобы начать, выберите роль:" + CANCEL_HINT,
        reply_markup=role_kb(),
    )
    await state.set_state(Onboarding.role)

@router.callback_query(F.data == "cancel")
async def cancel_flow_cb(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await upsert_text(cb, "Ок, отменил", reply_markup=main_menu())
    await cb.answer()

@router.message(F.text.in_({"отмена", "cancel", "/cancel"}))
async def cancel_flow_msg(message: Message, state: FSMContext):
    await state.clear()
    await upsert_text(message, "Ок, отменил", reply_markup=main_menu())

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) == 2 and parts[1].startswith("cargo_"):
            try:
                cargo_id = int(parts[1].split("_")[1])
            except:
                cargo_id = None
            if cargo_id:
                await send_cargo_details(message, cargo_id)
                return

    async with async_session() as session:
        user = await session.get(User, message.from_user.id)

    if user and user.is_verified:
        await state.clear()
        await message.answer("Меню:", reply_markup=main_menu())
        return

    if await needs_onboarding(message.from_user.id):
        await start_onboarding(message, state)
        return

    await message.answer(
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n\n"
        "Выбери действие в меню ниже.",
        reply_markup=main_menu(),
    )

@router.callback_query(F.data == "menu")
async def show_menu(cb: CallbackQuery):
    try:
        await cb.message.edit_text("🏠 <b>Главное меню</b>", reply_markup=main_menu())
    except TelegramBadRequest:
        await cb.message.answer("🏠 <b>Главное меню</b>", reply_markup=main_menu())
    await cb.answer()

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
        if not user:
            user = User(id=cb.from_user.id, username=cb.from_user.username, full_name=cb.from_user.full_name)
            session.add(user)
        user.is_carrier = role == UserRole.CARRIER
        await session.commit()

    await state.update_data(role=role.value)
    await upsert_text(
        cb,
        "📲 Поделись номером телефона через кнопку ниже." + CANCEL_HINT,
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
        if not user:
            user = User(id=message.from_user.id, username=message.from_user.username, full_name=message.from_user.full_name)
            session.add(user)
        user.phone = phone
        await session.commit()

    data = await state.get_data()
    role_value = data.get("role")
    role = UserRole(role_value) if role_value else profile.role

    if not role:
        await upsert_text(
            message,
            "Выберите роль, чтобы продолжить:",
            reply_markup=role_kb(),
        )
        await state.set_state(Onboarding.role)
        return

    if role == UserRole.CARRIER:
        await upsert_text(
            message,
            "✅ Номер сохранён.\n\n🏢 Укажите тип организации:" + CANCEL_HINT,
            reply_markup=legal_type_kb(),
        )
        await state.set_state(Onboarding.legal_type)
        return

    await upsert_text(
        message,
        "✅ Номер сохранён.\n\n🧾 Укажи ИНН (10 или 12 цифр):" + CANCEL_HINT,
    )
    await state.set_state(Onboarding.inn)

@router.message(Onboarding.legal_type)
async def onboarding_legal_type(message: Message, state: FSMContext):
    legal_type = message.text.strip()
    if legal_type not in ("ИП", "ООО", "Физлицо"):
        await upsert_text(
            message,
            "❌ Выбери тип из кнопок ниже.",
            reply_markup=legal_type_kb(),
        )
        return

    if legal_type == "Физлицо":
        async with async_session() as session:
            user = (await session.execute(select(User).where(User.id == message.from_user.id))).scalar_one_or_none()
            profile = await ensure_profile(session, message.from_user.id)
            profile.inn = None
            if user:
                user.company = None
            await session.commit()

        await state.clear()
        await upsert_text(
            message,
            "✅ Регистрация завершена",
            reply_markup=main_menu(),
        )
        return

    await upsert_text(
        message,
        "🧾 Укажи ИНН (10 или 12 цифр):" + CANCEL_HINT,
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(Onboarding.inn)

@router.message(Onboarding.inn)
async def onboarding_inn(message: Message, state: FSMContext):
    inn = message.text.strip()
    if not inn.isdigit() or len(inn) not in (10, 12):
        await upsert_text(message, "❌ ИНН должен содержать 10 или 12 цифр")
        return

    async with async_session() as session:
        profile = await ensure_profile(session, message.from_user.id)
        profile.inn = inn
        await session.commit()

    await upsert_text(message, "🏢 Введи название компании (ООО/ИП):" + CANCEL_HINT)
    await state.set_state(Onboarding.company)

@router.message(Onboarding.company)
async def onboarding_company(message: Message, state: FSMContext):
    company = message.text.strip()
    if not company:
        await upsert_text(message, "❌ Введи название компании")
        return

    async with async_session() as session:
        user = (await session.execute(select(User).where(User.id == message.from_user.id))).scalar_one_or_none()
        profile = await ensure_profile(session, message.from_user.id)
        if not user:
            user = User(id=message.from_user.id, username=message.from_user.username, full_name=message.from_user.full_name)
            session.add(user)
        user.company = company
        await session.commit()

    await state.clear()
    await upsert_text(
        message,
        "✅ Регистрация завершена",
        reply_markup=main_menu(),
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📚 <b>Как пользоваться:</b>\n\n"
        "Основные действия — через кнопки меню:\n"
        "🚛 Найти груз\n"
        "📦 Разместить груз\n"
        "🧾 Мои грузы\n"
        "🤝 Мои отклики\n"
        "⭐ Рейтинг / Профиль\n"
        "🆘 Поддержка\n\n"
        "<b>Команды:</b>\n"
        "/start — меню\n"
        "/help — помощь\n"
        "/me — мой профиль\n"
        "/remind 30m Текст — напоминание\n"
        "/reminders — мои напоминания"
    )

@router.message(Command("me"))
async def cmd_me(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == message.from_user.id))
        user = result.scalar_one_or_none()

        reminders = await session.execute(
            select(Reminder)
            .where(Reminder.user_id == message.from_user.id)
            .where(Reminder.is_sent == False)
        )
        rem_count = len(reminders.scalars().all())

    if user:
        status = "🚫 Забанен" if user.is_banned else "✅ Активен"
        await message.answer(
            "👤 <b>Твой профиль:</b>\n\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"📝 Имя: {user.full_name}\n"
            f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}\n"
            f"⏰ Напоминаний: {rem_count}\n"
            f"Статус: {status}"
        )
