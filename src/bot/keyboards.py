from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📝 Фидбек", callback_data="feedback"))
    b.row(InlineKeyboardButton(text="ℹ️ О боте", callback_data="about"))
    return b.as_markup()

def confirm_kb():
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Да", callback_data="yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="no")
    )
    return b.as_markup()
