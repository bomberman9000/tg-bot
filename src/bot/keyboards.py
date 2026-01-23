from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🚛 Грузы", callback_data="cargos"))
    b.row(InlineKeyboardButton(text="📦 Добавить груз", callback_data="add_cargo"))
    b.row(InlineKeyboardButton(text="👤 Профиль", callback_data="profile"))
    b.row(InlineKeyboardButton(text="📝 Фидбек", callback_data="feedback"))
    return b.as_markup()

def confirm_kb():
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Да", callback_data="yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="no")
    )
    return b.as_markup()

def cargo_actions(cargo_id: int, is_owner: bool = False):
    b = InlineKeyboardBuilder()
    if is_owner:
        b.row(InlineKeyboardButton(text="📋 Отклики", callback_data=f"responses_{cargo_id}"))
        b.row(InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{cargo_id}"))
    else:
        b.row(InlineKeyboardButton(text="📞 Откликнуться", callback_data=f"respond_{cargo_id}"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="cargos"))
    return b.as_markup()

def cargos_menu():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📋 Все грузы", callback_data="all_cargos"))
    b.row(InlineKeyboardButton(text="📦 Мои грузы", callback_data="my_cargos"))
    b.row(InlineKeyboardButton(text="🚛 Мои отклики", callback_data="my_responses"))
    b.row(InlineKeyboardButton(text="◀️ Меню", callback_data="menu"))
    return b.as_markup()

def back_menu():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="◀️ Меню", callback_data="menu"))
    return b.as_markup()

def skip_kb():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip"))
    return b.as_markup()
