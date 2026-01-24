from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🚛 Грузы", callback_data="cargos"))
    b.row(InlineKeyboardButton(text="📦 Добавить груз", callback_data="add_cargo"))
    b.row(InlineKeyboardButton(text="🔔 Подписки", callback_data="subscriptions"))
    b.row(InlineKeyboardButton(text="📊 Аналитика", callback_data="analytics"))
    b.row(InlineKeyboardButton(text="💬 Сообщения", callback_data="messages"))
    b.row(InlineKeyboardButton(text="👤 Профиль", callback_data="profile"))
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
        b.row(InlineKeyboardButton(text="✅ Завершить", callback_data=f"complete_{cargo_id}"))
        b.row(InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{cargo_id}"))
    else:
        b.row(InlineKeyboardButton(text="📞 Откликнуться", callback_data=f"respond_{cargo_id}"))
        b.row(InlineKeyboardButton(text="💬 Написать", callback_data=f"chat_{cargo_id}"))
    b.row(InlineKeyboardButton(text="📄 ТТН", callback_data=f"ttn_{cargo_id}"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="cargos"))
    return b.as_markup()

def cargos_menu():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📋 Все грузы", callback_data="all_cargos"))
    b.row(InlineKeyboardButton(text="🔍 Поиск", callback_data="search_cargo"))
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

def response_actions(response_id: int):
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{response_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{response_id}")
    )
    return b.as_markup()

def subscriptions_menu():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="➕ Добавить подписку", callback_data="add_subscription"))
    b.row(InlineKeyboardButton(text="📋 Мои подписки", callback_data="my_subscriptions"))
    b.row(InlineKeyboardButton(text="◀️ Меню", callback_data="menu"))
    return b.as_markup()

def analytics_menu():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💰 Мой заработок", callback_data="my_earnings"))
    b.row(InlineKeyboardButton(text="📊 Мои маршруты", callback_data="my_routes"))
    b.row(InlineKeyboardButton(text="🔥 Популярные маршруты", callback_data="popular_routes"))
    b.row(InlineKeyboardButton(text="📈 Средние цены", callback_data="avg_prices"))
    b.row(InlineKeyboardButton(text="◀️ Меню", callback_data="menu"))
    return b.as_markup()

def profile_menu():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📞 Изменить телефон", callback_data="edit_phone"))
    b.row(InlineKeyboardButton(text="🏢 Изменить компанию", callback_data="edit_company"))
    b.row(InlineKeyboardButton(text="📦 Мои грузы", callback_data="my_cargos"))
    b.row(InlineKeyboardButton(text="📜 История", callback_data="history"))
    b.row(InlineKeyboardButton(text="◀️ Меню", callback_data="menu"))
    return b.as_markup()

def chat_kb(cargo_id: int, user_id: int):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✏️ Ответить", callback_data=f"reply_{cargo_id}_{user_id}"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="messages"))
    return b.as_markup()
