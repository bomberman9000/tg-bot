from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.core.models import CargoStatus, Cargo

def main_menu():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🚛 Найти груз", callback_data="search_cargo"))
    b.row(InlineKeyboardButton(text="📦 Разместить груз", callback_data="add_cargo"))
    b.row(InlineKeyboardButton(text="🧾 Мои грузы", callback_data="my_cargos"))
    b.row(InlineKeyboardButton(text="🤝 Мои отклики", callback_data="my_responses"))
    b.row(InlineKeyboardButton(text="⭐ Рейтинг / Профиль", callback_data="profile"))
    b.row(InlineKeyboardButton(text="🆘 Поддержка", callback_data="feedback"))
    return b.as_markup()

def confirm_kb():
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Да", callback_data="yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="no")
    )
    return b.as_markup()

def cargo_actions(
    cargo_id: int,
    is_owner: bool,
    status: CargoStatus,
    owner_company_id: int | None = None,
):
    b = InlineKeyboardBuilder()
    if is_owner:
        if status != CargoStatus.ARCHIVED:
            b.row(InlineKeyboardButton(text="👥 Отклики", callback_data=f"responses_{cargo_id}"))
            b.row(InlineKeyboardButton(text="✅ Завершить", callback_data=f"complete_{cargo_id}"))
            b.row(InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{cargo_id}"))
        if status == CargoStatus.NEW:
            b.row(InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_cargo_{cargo_id}"))
            b.row(InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{cargo_id}"))
        if status == CargoStatus.ARCHIVED:
            b.row(InlineKeyboardButton(text="♻️ Восстановить", callback_data=f"restore_cargo_{cargo_id}"))
    else:
        b.row(InlineKeyboardButton(text="📨 Откликнуться", callback_data=f"respond_{cargo_id}"))
        if owner_company_id is not None:
            b.row(
                InlineKeyboardButton(
                    text="🏢 Профиль заказчика",
                    callback_data=f"company_profile_{owner_company_id}",
                )
            )
    b.row(InlineKeyboardButton(text="📄 ТТН", callback_data=f"ttn_{cargo_id}"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="cargos"))
    return b.as_markup()

def cargo_edit_kb(cargo_id: int):
    """Клавиатура выбора что редактировать"""
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_price_{cargo_id}"))
    b.row(InlineKeyboardButton(text="📅 Дата загрузки", callback_data=f"edit_date_{cargo_id}"))
    b.row(InlineKeyboardButton(text="🕐 Время загрузки", callback_data=f"edit_time_{cargo_id}"))
    b.row(InlineKeyboardButton(text="💬 Комментарий", callback_data=f"edit_comment_{cargo_id}"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data=f"cargo_open_{cargo_id}"))
    return b.as_markup()

def my_cargos_kb(cargos: list[Cargo]):
    b = InlineKeyboardBuilder()
    for c in cargos:
        title = f"{c.from_city} → {c.to_city} | {c.weight}т | {c.price}₽"
        b.row(InlineKeyboardButton(text=title[:64], callback_data=f"cargo_open_{c.id}"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="cargos"))
    return b.as_markup()

def delete_confirm_kb(cargo_id: int):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delete_yes_{cargo_id}"))
    b.row(InlineKeyboardButton(text="❌ Нет", callback_data=f"delete_no_{cargo_id}"))
    return b.as_markup()

def cargo_open_list_kb(cargos, back_cb: str = "cargos") -> InlineKeyboardMarkup:
    """Список грузов: кнопки «Открыть #id» + Назад."""
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for c in cargos:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"Открыть #{c.id}",
                callback_data=f"cargo_open_{c.id}",
            )
        ])

    kb.inline_keyboard.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data=back_cb)
    ])
    return kb


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

def price_suggest_kb(suggested_price: int | None = None):
    b = InlineKeyboardBuilder()
    if suggested_price:
        b.row(
            InlineKeyboardButton(
                text=f"✅ {suggested_price:,} ₽ (рекомендуемая)",
                callback_data=f"use_price_{suggested_price}",
            )
        )
    b.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return b.as_markup()

def response_actions(
    response_id: int,
    carrier_company_id: int | None = None,
):
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Выбрать", callback_data=f"accept_{response_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{response_id}"),
    )
    if carrier_company_id is not None:
        b.row(
            InlineKeyboardButton(
                text="🏢 Профиль компании",
                callback_data=f"company_profile_{carrier_company_id}",
            )
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
    b.row(InlineKeyboardButton(text="✅ Пройти верификацию", callback_data="start_verification"))
    b.row(InlineKeyboardButton(text="🔍 Проверить контрагента", callback_data="legal_check"))
    b.row(InlineKeyboardButton(text="💬 Сообщения", callback_data="messages"))
    b.row(InlineKeyboardButton(text="📋 Мои претензии", callback_data="my_claims"))
    b.row(InlineKeyboardButton(text="🔔 Подписки", callback_data="subscriptions"))
    b.row(InlineKeyboardButton(text="📊 Аналитика", callback_data="analytics"))
    b.row(InlineKeyboardButton(text="🛡 Безопасность", callback_data="antifraud"))
    b.row(InlineKeyboardButton(text="📦 Мои грузы", callback_data="my_cargos"))
    b.row(InlineKeyboardButton(text="📜 История", callback_data="history"))
    b.row(InlineKeyboardButton(text="◀️ Меню", callback_data="menu"))
    return b.as_markup()


def claim_type_kb():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💰 Неоплата", callback_data="claim_type_payment"))
    b.row(InlineKeyboardButton(text="📦 Повреждение груза", callback_data="claim_type_damage"))
    b.row(InlineKeyboardButton(text="⏰ Срыв сроков", callback_data="claim_type_delay"))
    b.row(InlineKeyboardButton(text="🚨 Мошенничество", callback_data="claim_type_fraud"))
    b.row(InlineKeyboardButton(text="❓ Другое", callback_data="claim_type_other"))
    b.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return b.as_markup()


def company_actions_kb(company_id: int, viewer_id: int):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📝 Подать претензию", callback_data=f"new_claim_{company_id}"))
    b.row(InlineKeyboardButton(text="📋 Претензии компании", callback_data=f"company_claims_{company_id}"))
    b.row(InlineKeyboardButton(text="🔍 Проверить в реестрах", callback_data=f"check_company_{company_id}"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="menu"))
    return b.as_markup()

def chat_kb(cargo_id: int, user_id: int):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✏️ Ответить", callback_data=f"reply_{cargo_id}_{user_id}"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="messages"))
    return b.as_markup()


def role_kb():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="Я заказчик", callback_data="role_customer"))
    b.row(InlineKeyboardButton(text="Я перевозчик", callback_data="role_carrier"))
    b.row(InlineKeyboardButton(text="Я экспедитор", callback_data="role_forwarder"))
    return b.as_markup()


def contact_request_kb():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,
        keyboard=[[KeyboardButton(text="📲 Поделиться номером", request_contact=True)]]
    )

def legal_type_kb():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,
        keyboard=[
            [KeyboardButton(text="ИП"), KeyboardButton(text="ООО")],
            [KeyboardButton(text="Физлицо")],
        ],
    )

def city_kb(cities: list[str], field: str):
    b = InlineKeyboardBuilder()
    for city in cities:
        b.row(InlineKeyboardButton(text=city, callback_data=f"city:{field}:{city}"))
    b.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return b.as_markup()


def deal_actions(cargo_id: int, is_owner: bool = False):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🗺 Трекинг", callback_data=f"tracking_{cargo_id}"))
    b.row(InlineKeyboardButton(text="💬 Чат", callback_data=f"chat_{cargo_id}"))
    b.row(InlineKeyboardButton(text="📄 Документы", callback_data=f"ttn_{cargo_id}"))
    if is_owner:
        b.row(InlineKeyboardButton(text="✅ Завершить", callback_data=f"complete_{cargo_id}"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="cargos"))
    return b.as_markup()
