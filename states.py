from aiogram.fsm.state import StatesGroup, State


class BookingStates(StatesGroup):
    """
    Состояния FSM для процесса бронирования фотосессии.
    """
    waiting_service = State()  # Ожидание выбора услуги
    waiting_date = State()     # Ожидание ввода даты
    waiting_time = State()     # Ожидание выбора времени
    confirm = State()          # Ожидание подтверждения бронирования
