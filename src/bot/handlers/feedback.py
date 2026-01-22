from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from src.bot.states import FeedbackForm
from src.bot.keyboards import confirm_keyboard, main_menu
from src.core.logger import logger
from src.core.redis import get_redis

router = Router()

@router.callback_query(F.data == "feedback")
async def start_feedback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Как тебя зовут?")
    await state.set_state(FeedbackForm.waiting_for_name)
    await callback.answer()

@router.message(FeedbackForm.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Отлично! Теперь напиши своё сообщение:")
    await state.set_state(FeedbackForm.waiting_for_message)

@router.message(FeedbackForm.waiting_for_message)
async def process_message(message: Message, state: FSMContext):
    await state.update_data(message=message.text)
    data = await state.get_data()
    
    text = f"📝 <b>Подтверди отправку:</b>\n\n"
    text += f"<b>Имя:</b> {data['name']}\n"
    text += f"<b>Сообщение:</b> {data['message']}"
    
    await message.answer(text, reply_markup=confirm_keyboard())
    await state.set_state(FeedbackForm.confirm)

@router.callback_query(FeedbackForm.confirm, F.data == "confirm_yes")
async def confirm_feedback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Сохраняем в Redis
    redis = await get_redis()
    await redis.lpush("feedback", f"{data['name']}: {data['message']}")
    
    logger.info(f"Feedback from {data['name']}: {data['message']}")
    
    await callback.message.edit_text("✅ Спасибо! Сообщение отправлено.")
    await state.clear()
    await callback.answer()

@router.callback_query(FeedbackForm.confirm, F.data == "confirm_no")
async def cancel_feedback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Отменено", reply_markup=main_menu())
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "about")
async def about(callback: CallbackQuery):
    await callback.message.edit_text(
        "🤖 <b>TG Bot Template</b>\n\n"
        "FastAPI + Aiogram + Redis\n"
        "by @bomberman9000",
        reply_markup=main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "stats")
async def stats(callback: CallbackQuery):
    redis = await get_redis()
    feedback_count = await redis.llen("feedback")
    
    await callback.message.edit_text(
        f"📊 <b>Статистика</b>\n\n"
        f"Сообщений: {feedback_count}",
        reply_markup=main_menu()
    )
    await callback.answer()
