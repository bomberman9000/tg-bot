from aiogram.fsm.state import State, StatesGroup

class FeedbackForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_message = State()
    confirm = State()
