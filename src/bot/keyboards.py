from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_yes"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="confirm_no")
    )
    return builder.as_markup()

def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Обратная связь", callback_data="feedback"),
        InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
    )
    return builder.as_markup()
