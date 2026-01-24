from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, or_
from datetime import datetime
from src.bot.states import CargoForm
from src.bot.keyboards import main_menu, confirm_kb, cargo_actions, cargos_menu, skip_kb, response_actions
from src.core.database import async_session
from src.core.models import Cargo, CargoStatus, CargoResponse, User, RouteSubscription
from src.core.documents import generate_ttn
from src.core.logger import logger
from src.bot.bot import bot

router = Router()

@router.callback_query(F.data == "cargos")
async def cargos_handler(cb: CallbackQuery):
    try:
        await cb.message.edit_text("🚛 <b>Грузы</b>", reply_markup=cargos_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.callback_query(F.data == "all_cargos")
async def all_cargos(cb: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Cargo).where(Cargo.status == CargoStatus.NEW).limit(10)
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
        text += f"🔹 {c.from_city} → {c.to_city}\n"
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
            select(Cargo).where(Cargo.owner_id == cb.from_user.id).limit(10)
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
        status_icon = {"new": "🆕", "in_progress": "🚚", "completed": "✅", "cancelled": "❌"}.get(c.status.value, "❓")
        text += f"{status_icon} {c.from_city} → {c.to_city}\n"
        text += f"   {c.weight}т, {c.price}₽ /cargo_{c.id}\n\n"
    
    try:
        await cb.message.edit_text(text, reply_markup=cargos_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.callback_query(F.data == "my_responses")
async def my_responses(cb: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(CargoResponse).where(CargoResponse.carrier_id == cb.from_user.id).limit(10)
        )
        responses = result.scalars().all()
    
    if not responses:
        try:
            await cb.message.edit_text("📭 Нет откликов", reply_markup=cargos_menu())
        except TelegramBadRequest:
            pass
        await cb.answer()
        return
    
    text = "🚛 <b>Мои отклики:</b>\n\n"
    for r in responses:
        status = "⏳" if r.is_accepted is None else ("✅" if r.is_accepted else "❌")
        text += f"{status} Груз #{r.cargo_id} — {r.price_offer or 'без цены'}₽ /cargo_{r.cargo_id}\n"
    
    try:
        await cb.message.edit_text(text, reply_markup=cargos_menu())
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.callback_query(F.data == "add_cargo")
async def add_cargo_start(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("🚛 <b>Новый груз</b>\n\nОткуда?")
    await state.set_state(CargoForm.from_city)
    await cb.answer()

@router.message(CargoForm.from_city)
async def cargo_from(message: Message, state: FSMContext):
    await state.update_data(from_city=message.text)
    await message.answer("Куда?")
    await state.set_state(CargoForm.to_city)

@router.message(CargoForm.to_city)
async def cargo_to(message: Message, state: FSMContext):
    await state.update_data(to_city=message.text)
    await message.answer("Тип груза? (например: паллеты, сборный)")
    await state.set_state(CargoForm.cargo_type)

@router.message(CargoForm.cargo_type)
async def cargo_type(message: Message, state: FSMContext):
    await state.update_data(cargo_type=message.text)
    await message.answer("Вес (тонн)?")
    await state.set_state(CargoForm.weight)

@router.message(CargoForm.weight)
async def cargo_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", "."))
        await state.update_data(weight=weight)
        await message.answer("Цена (₽)?")
        await state.set_state(CargoForm.price)
    except:
        await message.answer("❌ Введи число")

@router.message(CargoForm.price)
async def cargo_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.replace(" ", ""))
        await state.update_data(price=price)
        await message.answer("Дата загрузки? (ДД.ММ.ГГГГ или ДД.ММ)")
        await state.set_state(CargoForm.load_date)
    except:
        await message.answer("❌ Введи число")

@router.message(CargoForm.load_date)
async def cargo_date(message: Message, state: FSMContext):
    try:
        text = message.text
        if len(text.split(".")) == 2:
            text += f".{datetime.now().year}"
        load_date = datetime.strptime(text, "%d.%m.%Y")
        await state.update_data(load_date=load_date)
        await message.answer("Комментарий? (или пропусти)", reply_markup=skip_kb())
        await state.set_state(CargoForm.comment)
    except:
        await message.answer("❌ Формат: ДД.ММ.ГГГГ")

@router.message(CargoForm.comment)
async def cargo_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await show_confirm(message, state)

@router.callback_query(CargoForm.comment, F.data == "skip")
async def cargo_skip_comment(cb: CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    await show_confirm(cb.message, state)
    await cb.answer()

async def show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    text = f"📦 <b>Подтверди груз:</b>\n\n"
    text += f"📍 {data['from_city']} → {data['to_city']}\n"
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
        
        subs = await session.execute(
            select(RouteSubscription).where(
                RouteSubscription.is_active == True
            ).where(
                or_(
                    RouteSubscription.from_city.is_(None),
                    RouteSubscription.from_city.ilike(f"%{data['from_city']}%")
                )
            ).where(
                or_(
                    RouteSubscription.to_city.is_(None),
                    RouteSubscription.to_city.ilike(f"%{data['to_city']}%")
                )
            )
        )
        subscribers = subs.scalars().all()
    
    await state.clear()
    await cb.message.edit_text(f"✅ Груз #{cargo_id} создан!", reply_markup=main_menu())
    
    for sub in subscribers:
        if sub.user_id != cb.from_user.id:
            try:
                await bot.send_message(
                    sub.user_id,
                    f"🔔 Новый груз по твоему маршруту!\n\n"
                    f"📍 {data['from_city']} → {data['to_city']}\n"
                    f"⚖️ {data['weight']}т, 💰 {data['price']}₽\n"
                    f"/cargo_{cargo_id}"
                )
            except:
                pass
    
    await cb.answer()
    logger.info(f"Cargo {cargo_id} created by {cb.from_user.id}")

@router.callback_query(CargoForm.confirm, F.data == "no")
async def cargo_confirm_no(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("❌ Отменено", reply_markup=main_menu())
    await cb.answer()

@router.message(F.text.startswith("/cargo_"))
async def show_cargo(message: Message):
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
        
        owner = await session.execute(select(User).where(User.id == cargo.owner_id))
        owner = owner.scalar_one_or_none()
    
    status_map = {"new": "🆕 Новый", "in_progress": "🚚 В пути", "completed": "✅ Завершён", "cancelled": "❌ Отменён"}
    
    text = f"📦 <b>Груз #{cargo.id}</b>\n\n"
    text += f"📍 {cargo.from_city} → {cargo.to_city}\n"
    text += f"📦 {cargo.cargo_type}\n"
    text += f"⚖️ {cargo.weight} т\n"
    text += f"💰 {cargo.price} ₽\n"
    text += f"📅 {cargo.load_date.strftime('%d.%m.%Y')}\n"
    text += f"📊 {status_map.get(cargo.status.value, cargo.status.value)}\n"
    if cargo.comment:
        text += f"💬 {cargo.comment}\n"
    text += f"\n👤 Заказчик: {owner.full_name if owner else 'N/A'}"
    if owner and owner.phone:
        text += f" ({owner.phone})"
    
    if cargo.status == CargoStatus.IN_PROGRESS:
        text += f"\n\n🗺 Отслеживание: /track_{cargo.id}"
    
    is_owner = cargo.owner_id == message.from_user.id
    await message.answer(text, reply_markup=cargo_actions(cargo.id, is_owner))

@router.callback_query(F.data.startswith("respond_"))
async def respond_cargo(cb: CallbackQuery):
    cargo_id = int(cb.data.split("_")[1])
    
    async with async_session() as session:
        existing = await session.execute(
            select(CargoResponse)
            .where(CargoResponse.cargo_id == cargo_id)
            .where(CargoResponse.carrier_id == cb.from_user.id)
        )
        if existing.scalar_one_or_none():
            await cb.answer("❌ Ты уже откликался", show_alert=True)
            return
        
        response = CargoResponse(cargo_id=cargo_id, carrier_id=cb.from_user.id)
        session.add(response)
        await session.commit()
        
        cargo = await session.execute(select(Cargo).where(Cargo.id == cargo_id))
        cargo = cargo.scalar_one_or_none()
        
        if cargo:
            try:
                await bot.send_message(
                    cargo.owner_id,
                    f"📞 Новый отклик на груз #{cargo_id}!\n/cargo_{cargo_id}"
                )
            except:
                pass
    
    await cb.answer("✅ Отклик отправлен!", show_alert=True)
    logger.info(f"Response from {cb.from_user.id} to cargo {cargo_id}")

@router.callback_query(F.data.startswith("responses_"))
async def show_responses(cb: CallbackQuery):
    cargo_id = int(cb.data.split("_")[1])
    
    async with async_session() as session:
        result = await session.execute(
            select(CargoResponse).where(CargoResponse.cargo_id == cargo_id)
        )
        responses = result.scalars().all()
    
    if not responses:
        await cb.answer("📭 Нет откликов", show_alert=True)
        return
    
    text = f"📋 <b>Отклики на груз #{cargo_id}:</b>\n\n"
    for r in responses:
        async with async_session() as session:
            user = await session.execute(select(User).where(User.id == r.carrier_id))
            user = user.scalar_one_or_none()
        
        status = "⏳" if r.is_accepted is None else ("✅" if r.is_accepted else "❌")
        name = user.full_name if user else f"ID:{r.carrier_id}"
        text += f"{status} {name}\n"
        if r.is_accepted is None:
            text += f"   /accept_{r.id} | /reject_{r.id}\n"
    
    try:
        await cb.message.edit_text(text, reply_markup=cargo_actions(cargo_id, True))
    except TelegramBadRequest:
        pass
    await cb.answer()

@router.message(F.text.startswith("/accept_"))
async def accept_response(message: Message):
    try:
        response_id = int(message.text.split("_")[1])
    except:
        return
    
    async with async_session() as session:
        result = await session.execute(select(CargoResponse).where(CargoResponse.id == response_id))
        response = result.scalar_one_or_none()
        
        if not response:
            await message.answer("❌ Отклик не найден")
            return
        
        cargo = await session.execute(select(Cargo).where(Cargo.id == response.cargo_id))
        cargo = cargo.scalar_one_or_none()
        
        if cargo.owner_id != message.from_user.id:
            await message.answer("❌ Нет доступа")
            return
        
        response.is_accepted = True
        cargo.carrier_id = response.carrier_id
        cargo.status = CargoStatus.IN_PROGRESS
        await session.commit()
        
        try:
            await bot.send_message(
                response.carrier_id,
                f"✅ Твой отклик на груз #{cargo.id} принят!\n\n"
                f"📍 {cargo.from_city} → {cargo.to_city}\n"
                f"🗺 Отслеживание: /track_{cargo.id}"
            )
        except:
            pass
    
    await message.answer(f"✅ Перевозчик назначен на груз #{cargo.id}")
    logger.info(f"Response {response_id} accepted")

@router.message(F.text.startswith("/reject_"))
async def reject_response(message: Message):
    try:
        response_id = int(message.text.split("_")[1])
    except:
        return
    
    async with async_session() as session:
        result = await session.execute(select(CargoResponse).where(CargoResponse.id == response_id))
        response = result.scalar_one_or_none()
        
        if not response:
            await message.answer("❌ Отклик не найден")
            return
        
        cargo = await session.execute(select(Cargo).where(Cargo.id == response.cargo_id))
        cargo = cargo.scalar_one_or_none()
        
        if cargo.owner_id != message.from_user.id:
            await message.answer("❌ Нет доступа")
            return
        
        response.is_accepted = False
        await session.commit()
    
    await message.answer("❌ Отклик отклонён")
    logger.info(f"Response {response_id} rejected")

@router.callback_query(F.data.startswith("complete_"))
async def complete_cargo(cb: CallbackQuery):
    cargo_id = int(cb.data.split("_")[1])
    
    async with async_session() as session:
        result = await session.execute(select(Cargo).where(Cargo.id == cargo_id))
        cargo = result.scalar_one_or_none()
        
        if not cargo or cargo.owner_id != cb.from_user.id:
            await cb.answer("❌ Нет доступа", show_alert=True)
            return
        
        cargo.status = CargoStatus.COMPLETED
        await session.commit()
        
        if cargo.carrier_id:
            try:
                await bot.send_message(
                    cargo.carrier_id,
                    f"✅ Груз #{cargo_id} завершён!\n\nОцени заказчика: /rate_{cargo_id}"
                )
            except:
                pass
    
    await cb.message.edit_text(
        f"✅ Груз #{cargo_id} завершён!\n\nОцени перевозчика: /rate_{cargo_id}",
        reply_markup=main_menu()
    )
    await cb.answer()
    logger.info(f"Cargo {cargo_id} completed")

@router.callback_query(F.data.startswith("cancel_"))
async def cancel_cargo(cb: CallbackQuery):
    cargo_id = int(cb.data.split("_")[1])
    
    async with async_session() as session:
        result = await session.execute(select(Cargo).where(Cargo.id == cargo_id))
        cargo = result.scalar_one_or_none()
        
        if not cargo or cargo.owner_id != cb.from_user.id:
            await cb.answer("❌ Нет доступа", show_alert=True)
            return
        
        cargo.status = CargoStatus.CANCELLED
        await session.commit()
    
    await cb.message.edit_text(f"❌ Груз #{cargo_id} отменён", reply_markup=main_menu())
    await cb.answer()
    logger.info(f"Cargo {cargo_id} cancelled")

@router.callback_query(F.data.startswith("ttn_"))
async def send_ttn(cb: CallbackQuery):
    cargo_id = int(cb.data.split("_")[1])
    
    async with async_session() as session:
        result = await session.execute(select(Cargo).where(Cargo.id == cargo_id))
        cargo = result.scalar_one_or_none()
        
        if not cargo:
            await cb.answer("❌ Груз не найден", show_alert=True)
            return
        
        owner = await session.execute(select(User).where(User.id == cargo.owner_id))
        owner = owner.scalar_one_or_none()
        
        carrier = None
        if cargo.carrier_id:
            carrier_result = await session.execute(select(User).where(User.id == cargo.carrier_id))
            carrier = carrier_result.scalar_one_or_none()
    
    pdf_buffer = generate_ttn(cargo, owner, carrier)
    
    await cb.message.answer_document(
        BufferedInputFile(pdf_buffer.read(), filename=f"TTN_{cargo_id}.pdf"),
        caption=f"📄 ТТН для груза #{cargo_id}"
    )
    await cb.answer()
    logger.info(f"TTN generated for cargo {cargo_id}")
