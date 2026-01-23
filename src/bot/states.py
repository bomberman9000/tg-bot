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
class SearchCargo(StatesGroup):
    from_city = State()
    to_city = State()

class SubscribeRoute(StatesGroup):
    from_city = State()
    to_city = State()
class RateForm(StatesGroup):
    score = State()
    comment = State()
class ProfileEdit(StatesGroup):
    phone = State()
    company = State()

class CargoFilter(StatesGroup):
    weight_min = State()
    weight_max = State()
    price_min = State()
    price_max = State()
