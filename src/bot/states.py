from aiogram.fsm.state import State, StatesGroup

class FeedbackForm(StatesGroup):
    message = State()
    confirm = State()

class CargoForm(StatesGroup):
    from_city = State()
    to_city = State()
    cargo_type = State()
    weight = State()
    price = State()
    load_date = State()
    comment = State()
    confirm = State()

class CarrierRegister(StatesGroup):
    phone = State()
    confirm = State()
