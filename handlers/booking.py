import json
from datetime import datetime, timedelta
from pathlib import Path
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import PHOTOGRAPHERS

router = Router()

# Файл для хранения записей
APPOINTMENTS_FILE = Path("data/appointments.json")

# Загрузка записей
def load_appointments():
    """Загружает записи из JSON файла"""
    if APPOINTMENTS_FILE.exists():
        with open(APPOINTMENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Сохранение записей
def save_appointments(appointments):
    """Сохраняет записи в JSON файл"""
    APPOINTMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(APPOINTMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(appointments, f, ensure_ascii=False, indent=2)

# Добавление записи
def add_appointment(user_id: int, user_name: str, photographer_id: str, date: str, time_slot: str):
    """Добавляет новую запись"""
    appointments = load_appointments()
    appointment = {
        "id": len(appointments) + 1,
        "user_id": user_id,
        "user_name": user_name,
        "photographer_id": photographer_id,
        "photographer_name": PHOTOGRAPHERS.get(photographer_id, {}).get("name", "Unknown"),
        "date": date,
        "time_slot": time_slot,
        "status": "new",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    appointments.append(appointment)
    save_appointments(appointments)
    return appointment

# FSM состояния для процесса записи
class BookingStates(StatesGroup):
    waiting_photographer = State()  # Ожидание выбора фотографа
    waiting_date = State()          # Ожидание выбора даты
    waiting_time = State()          # Ожидание выбора времени
    confirm = State()               # Подтверждение записи

# Обработчик кнопки "📅 Запись"
@router.callback_query(F.data == "booking")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    """Начало процесса записи - выбор фотографа"""
    await state.set_state(BookingStates.waiting_photographer)
    
    # Создаем кнопки с фотографами
    keyboard_buttons = []
    for photographer_id, photographer_data in PHOTOGRAPHERS.items():
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📸 {photographer_data['name']}",
                callback_data=f"book_photographer_{photographer_id}"
            )
        ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(
        "📅 Запись на фотосессию\n\n"
        "Выберите фотографа:",
        reply_markup=keyboard
    )
    await callback.answer()

# Выбор фотографа
@router.callback_query(BookingStates.waiting_photographer, F.data.startswith("book_photographer_"))
async def select_photographer(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора фотографа"""
    photographer_id = callback.data.replace("book_photographer_", "")
    
    if photographer_id not in PHOTOGRAPHERS:
        await callback.answer("❌ Фотограф не найден!", show_alert=True)
        return
    
    # Сохраняем выбранного фотографа
    await state.update_data(photographer_id=photographer_id)
    await state.set_state(BookingStates.waiting_date)
    
    # Генерируем календарь на неделю вперед
    await show_calendar(callback, state)

# Показать календарь с днями недели
async def show_calendar(callback: CallbackQuery, state: FSMContext):
    """Отображение календаря с доступными датами"""
    today = datetime.now().date()
    
    # Генерируем даты на ближайшие 7 дней
    dates = []
    for i in range(7):
        date = today + timedelta(days=i)
        dates.append(date)
    
    # Создаем кнопки с днями недели
    keyboard_buttons = []
    row = []
    
    days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    months_ru = ["янв", "фев", "мар", "апр", "май", "июн", 
                 "июл", "авг", "сен", "окт", "ноя", "дек"]
    
    for i, date in enumerate(dates):
        day_name = days_ru[date.weekday()]
        date_str = date.strftime("%Y-%m-%d")
        date_display = f"{day_name} {date.day} {months_ru[date.month - 1]}"
        
        row.append(InlineKeyboardButton(
            text=date_display,
            callback_data=f"book_date_{date_str}"
        ))
        
        # По 2 кнопки в ряду
        if len(row) == 2 or i == len(dates) - 1:
            keyboard_buttons.append(row)
            row = []
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="booking")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    data = await state.get_data()
    photographer_name = PHOTOGRAPHERS[data["photographer_id"]]["name"]
    
    await callback.message.edit_text(
        f"📅 Выберите дату\n\n"
        f"📸 Фотограф: {photographer_name}\n\n"
        f"Доступные даты:",
        reply_markup=keyboard
    )
    await callback.answer()

# Выбор даты
@router.callback_query(BookingStates.waiting_date, F.data.startswith("book_date_"))
async def select_date(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    date_str = callback.data.replace("book_date_", "")
    
    # Сохраняем дату
    await state.update_data(date=date_str)
    await state.set_state(BookingStates.waiting_time)
    
    # Показываем временные слоты
    await show_time_slots(callback, state)

# Показать временные слоты
async def show_time_slots(callback: CallbackQuery, state: FSMContext):
    """Отображение доступных временных слотов"""
    data = await state.get_data()
    date_str = data.get("date")
    
    # Доступные временные слоты
    time_slots = [
        ("10:00", "10:00-12:00"),
        ("14:00", "14:00-16:00"),
        ("18:00", "18:00-20:00")
    ]
    
    keyboard_buttons = []
    for time_value, time_display in time_slots:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=time_display,
                callback_data=f"book_time_{time_value}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Назад к календарю", callback_data="book_back_to_calendar")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Форматируем дату для отображения
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    date_display = date_obj.strftime("%d.%m.%Y")
    
    await callback.message.edit_text(
        f"🕐 Выберите время\n\n"
        f"📅 Дата: {date_display}\n\n"
        f"Доступные слоты:",
        reply_markup=keyboard
    )
    await callback.answer()

# Выбор времени
@router.callback_query(BookingStates.waiting_time, F.data.startswith("book_time_"))
async def select_time(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    time_slot = callback.data.replace("book_time_", "")
    
    # Сохраняем время
    await state.update_data(time_slot=time_slot)
    await state.set_state(BookingStates.confirm)
    
    # Показываем подтверждение
    await show_confirmation(callback, state)

# Возврат к календарю
@router.callback_query(BookingStates.waiting_time, F.data == "book_back_to_calendar")
async def back_to_calendar(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору даты"""
    await state.set_state(BookingStates.waiting_date)
    await show_calendar(callback, state)

# Показать подтверждение
async def show_confirmation(callback: CallbackQuery, state: FSMContext):
    """Отображение подтверждения записи"""
    data = await state.get_data()
    
    photographer_id = data.get("photographer_id")
    photographer_name = PHOTOGRAPHERS[photographer_id]["name"]
    date_str = data.get("date")
    time_slot = data.get("time_slot")
    
    # Форматируем дату
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    date_display = date_obj.strftime("%d.%m.%Y")
    
    # Форматируем время
    time_display = {
        "10:00": "10:00-12:00",
        "14:00": "14:00-16:00",
        "18:00": "18:00-20:00"
    }.get(time_slot, time_slot)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="book_confirm"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="book_cancel")
        ]
    ])
    
    await callback.message.edit_text(
        f"📋 Подтвердите запись:\n\n"
        f"📸 Фотограф: {photographer_name}\n"
        f"📅 Дата: {date_display}\n"
        f"🕐 Время: {time_display}\n\n"
        f"Нажмите 'Подтвердить' для завершения записи.",
        reply_markup=keyboard
    )
    await callback.answer()

# Подтверждение записи
@router.callback_query(BookingStates.confirm, F.data == "book_confirm")
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и сохранение записи"""
    data = await state.get_data()
    
    photographer_id = data.get("photographer_id")
    photographer_name = PHOTOGRAPHERS[photographer_id]["name"]
    date_str = data.get("date")
    time_slot = data.get("time_slot")
    
    # Сохраняем запись в appointments.json
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name or callback.from_user.username or "Пользователь"
    
    appointment = add_appointment(user_id, user_name, photographer_id, date_str, time_slot)
    
    # Форматируем дату и время
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    date_display = date_obj.strftime("%d.%m.%Y")
    time_display = {
        "10:00": "10:00-12:00",
        "14:00": "14:00-16:00",
        "18:00": "18:00-20:00"
    }.get(time_slot, time_slot)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        f"✅ Запись успешно создана!\n\n"
        f"📸 Фотограф: {photographer_name}\n"
        f"📅 Дата: {date_display}\n"
        f"🕐 Время: {time_display}\n\n"
        f"Мы свяжемся с вами для подтверждения.",
        reply_markup=keyboard
    )
    
    await state.clear()
    await callback.answer("✅ Запись создана!")

# Отмена записи
@router.callback_query(BookingStates.confirm, F.data == "book_cancel")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    """Отмена записи"""
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        "❌ Запись отменена.",
        reply_markup=keyboard
    )
    await callback.answer()

# Обработчик "Мои записи"
@router.callback_query(F.data == "my_bookings")
async def show_my_bookings(callback: CallbackQuery):
    """Показывает список записей пользователя"""
    user_id = callback.from_user.id
    appointments = load_appointments()
    
    # Фильтруем записи пользователя
    user_appointments = [appt for appt in appointments if appt.get("user_id") == user_id]
    
    if not user_appointments:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📅 Записаться", callback_data="booking")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text(
            "📋 Мои записи\n\n"
            "❌ У вас пока нет записей.\n\n"
            "Хотите записаться?",
            reply_markup=keyboard
        )
        await callback.answer()
        return
    
    # Сортируем по дате (сначала ближайшие)
    user_appointments.sort(key=lambda x: x.get("date", ""))
    
    # Формируем текст
    bookings_text = "📋 Мои записи:\n\n"
    
    status_emojis = {
        "new": "🆕",
        "confirmed": "✅",
        "cancelled": "❌"
    }
    
    status_texts = {
        "new": "Новое",
        "confirmed": "Подтверждено",
        "cancelled": "Отменено"
    }
    
    for appt in user_appointments:
        photographer_name = appt.get("photographer_name", "Unknown")
        date_str = appt.get("date", "")
        time_slot = appt.get("time_slot", "")
        status = appt.get("status", "new")
        
        # Форматируем дату
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_display = date_obj.strftime("%d.%m.%Y")
        except:
            date_display = date_str
        
        # Форматируем время
        time_display = {
            "10:00": "10:00-12:00",
            "14:00": "14:00-16:00",
            "18:00": "18:00-20:00"
        }.get(time_slot, time_slot)
        
        status_emoji = status_emojis.get(status, "❓")
        status_text = status_texts.get(status, status)
        
        bookings_text += (
            f"{status_emoji} Запись #{appt.get('id', '?')}\n"
            f"📸 {photographer_name}\n"
            f"📅 {date_display} 🕐 {time_display}\n"
            f"📊 {status_text}\n\n"
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Новая запись", callback_data="booking")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        bookings_text,
        reply_markup=keyboard
    )
    await callback.answer()
