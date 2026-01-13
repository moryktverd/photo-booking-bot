from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter, Command
from keyboards import main_menu, services_menu
from database import db
# Убери импорты database/config отсюда ↓

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, db: Database):
    """
    Обработчик команды /start - показывает главное меню.
    """
    await message.answer(
        "👋 Добро пожаловать в бот для бронирования фотосессий!\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """
    Возврат в главное меню с очисткой состояния FSM.
    """
    await state.clear()
    await callback.message.edit_text(
        "👋 Добро пожаловать в бот для бронирования фотосессий!\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "services_info")
async def show_services_info(callback: CallbackQuery):
    """
    Показывает информацию об услугах.
    """
    services_text = (
        "📸 Наши услуги:\n\n"
        "👨‍👩‍👧 Семейная фотосессия - 5000₽\n"
        "   Идеально для создания семейных воспоминаний\n\n"
        "📷 Портретная фотосессия - 3000₽\n"
        "   Индивидуальные и профессиональные портреты\n\n"
        "💒 Свадебная фотосессия - 15000₽\n"
        "   Полное сопровождение вашего особенного дня\n\n"
        "Выберите услугу для бронирования:"
    )
    await callback.message.edit_text(
        services_text,
        reply_markup=get_services_info_keyboard()
    )


@router.callback_query(F.data == "book_service")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    """
    Начало процесса бронирования - выбор услуги.
    """
    await state.set_state(BookingStates.waiting_service)
    await callback.message.edit_text(
        "📸 Выберите услугу:",
        reply_markup=get_services_keyboard()
    )


@router.callback_query(
    BookingStates.waiting_service,
    F.data.startswith("service_")
)
async def select_service(callback: CallbackQuery, state: FSMContext):
    """
    Обработка выбора услуги и переход к вводу даты.
    """
    service = callback.data.split("_", 1)[1]
    
    # Словарь для получения цены
    service_prices = {
        "семейная": "5000₽",
        "портрет": "3000₽",
        "свадьба": "15000₽"
    }
    price = service_prices.get(service, "")
    
    await state.update_data(service=service)
    await state.set_state(BookingStates.waiting_date)
    
    service_names = {
        "семейная": "семейную фотосессию",
        "портрет": "портретную фотосессию",
        "свадьба": "свадебную фотосессию"
    }
    
    await callback.message.edit_text(
        f"✅ Выбрана услуга: {service}\n\n"
        f"📅 Введите дату в формате YYYY-MM-DD\n"
        f"(например: {datetime.now().strftime('%Y-%m-%d')}):"
    )


@router.message(BookingStates.waiting_date)
async def process_date(message: Message, state: FSMContext):
    """
    Обработка ввода даты с валидацией формата YYYY-MM-DD.
    """
    date_text = message.text.strip()
    
    # Проверка формата даты
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(date_pattern, date_text):
        await message.answer(
            "❌ Неверный формат даты!\n\n"
            "Пожалуйста, введите дату в формате YYYY-MM-DD\n"
            f"(например: {datetime.now().strftime('%Y-%m-%d')}):"
        )
        return
    
    # Проверка корректности даты
    try:
        input_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        today = datetime.now().date()
        
        if input_date < today:
            await message.answer(
                "❌ Нельзя выбрать прошедшую дату!\n\n"
                f"Пожалуйста, введите дату начиная с {today.strftime('%Y-%m-%d')}:"
            )
            return
        
        await state.update_data(date=date_text)
        data = await state.get_data()
        service = data.get("service", "")
        
        await state.set_state(BookingStates.waiting_time)
        await message.answer(
            f"✅ Дата выбрана: {date_text}\n\n"
            "🕐 Выберите время:",
            reply_markup=get_time_slots_keyboard(date_text, service)
        )
    except ValueError:
        await message.answer(
            "❌ Неверная дата!\n\n"
            "Пожалуйста, введите корректную дату в формате YYYY-MM-DD\n"
            f"(например: {datetime.now().strftime('%Y-%m-%d')}):"
        )


@router.callback_query(
    BookingStates.waiting_time,
    F.data.startswith("timeslot_")
)
async def select_time(callback: CallbackQuery, state: FSMContext):
    """
    Обработка выбора времени и переход к подтверждению.
    """
    # Парсинг callback_data: timeslot_{date}_{time}_{service}
    parts = callback.data.split("_", 1)[1].split("_")
    if len(parts) >= 2:
        date = parts[0]
        time_slot = parts[1]
        service = "_".join(parts[2:]) if len(parts) > 2 else ""
        
        await state.update_data(
            date=date,
            time_slot=time_slot,
            service=service
        )
        
        data = await state.get_data()
        
        service_names = {
            "семейная": "👨‍👩‍👧 Семейная фотосессия",
            "портрет": "📷 Портретная фотосессия",
            "свадьба": "💒 Свадебная фотосессия"
        }
        
        service_prices = {
            "семейная": "5000₽",
            "портрет": "3000₽",
            "свадьба": "15000₽"
        }
        
        time_display = {
            "10:00": "10:00-12:00",
            "14:00": "14:00-16:00",
            "18:00": "18:00-20:00"
        }
        
        confirmation_text = (
            "📋 Подтвердите бронирование:\n\n"
            f"Услуга: {service_names.get(service, service)}\n"
            f"Дата: {date}\n"
            f"Время: {time_display.get(time_slot, time_slot)}\n"
            f"Стоимость: {service_prices.get(service, '')}\n\n"
            "Нажмите 'Подтвердить' для завершения бронирования."
        )
        
        await state.set_state(BookingStates.confirm)
        await callback.message.edit_text(
            confirmation_text,
            reply_markup=get_confirm_booking_keyboard(0)  # ID будет установлен после сохранения
        )


@router.callback_query(
    BookingStates.confirm,
    F.data.startswith("confirm_booking_")
)
async def confirm_booking(callback: CallbackQuery, state: FSMContext, db: Database, bot: Any):
    """
    Подтверждение и сохранение бронирования в БД с уведомлением админа.
    """
    data = await state.get_data()
    
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name or callback.from_user.username or "Пользователь"
    service = data.get("service")
    date = data.get("date")
    time_slot = data.get("time_slot")
    
    if not all([service, date, time_slot]):
        await callback.answer("❌ Ошибка: не все данные заполнены", show_alert=True)
        await state.clear()
        await callback.message.edit_text(
            "❌ Произошла ошибка. Попробуйте начать заново.",
            reply_markup=get_back_to_main_keyboard()
        )
        return
    
    try:
        # Сохранение в БД
        booking_id = await db.add_booking(
            user_id=user_id,
            user_name=user_name,
            service=service,
            date=date,
            time_slot=time_slot,
            status="new"
        )
        
        service_names = {
            "семейная": "семейная",
            "портрет": "портретная",
            "свадьба": "свадебная"
        }
        
        time_display = {
            "10:00": "10:00-12:00",
            "14:00": "14:00-16:00",
            "18:00": "18:00-20:00"
        }
        
        # Уведомление пользователю
        success_text = (
            f"✅ Бронирование #{booking_id} успешно создано!\n\n"
            f"Услуга: {service_names.get(service, service)}\n"
            f"Дата: {date}\n"
            f"Время: {time_display.get(time_slot, time_slot)}\n\n"
            "Мы свяжемся с вами для подтверждения."
        )
        
        await callback.message.edit_text(
            success_text,
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer("✅ Бронирование создано!")
        
        # Уведомление админа
        admin_notification = (
            f"🆕 Новое бронирование #{booking_id}\n\n"
            f"👤 Пользователь: {user_name} (@{callback.from_user.username or 'без username'})\n"
            f"📸 Услуга: {service_names.get(service, service)}\n"
            f"📅 Дата: {date}\n"
            f"🕐 Время: {time_display.get(time_slot, time_slot)}\n"
            f"🆔 ID пользователя: {user_id}"
        )
        
        try:
            await bot.send_message(
                chat_id=PHOTO_ADMIN_ID,
                text=admin_notification
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления админу: {e}")
        
        await state.clear()
        
    except Exception as e:
        await callback.answer("❌ Ошибка при сохранении бронирования", show_alert=True)
        await callback.message.edit_text(
            "❌ Произошла ошибка при сохранении. Попробуйте позже.",
            reply_markup=get_back_to_main_keyboard()
        )
        await state.clear()
        print(f"Ошибка сохранения бронирования: {e}")


@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    """
    Отмена процесса бронирования.
    """
    await state.clear()
    await callback.message.edit_text(
        "❌ Бронирование отменено.",
        reply_markup=get_back_to_main_keyboard()
    )


@router.callback_query(F.data.startswith("back_to_services_"))
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    """
    Возврат к выбору услуги из выбора времени.
    """
    service = callback.data.split("_", 3)[3] if len(callback.data.split("_")) > 3 else ""
    
    await state.update_data(service=service)
    await state.set_state(BookingStates.waiting_service)
    await callback.message.edit_text(
        "📸 Выберите услугу:",
        reply_markup=get_services_keyboard()
    )


@router.callback_query(F.data == "my_bookings")
async def show_my_bookings(callback: CallbackQuery, db: Database):
    """
    Показывает список бронирований пользователя.
    """
    user_id = callback.from_user.id
    bookings = await db.get_user_bookings(user_id)
    
    if not bookings:
        await callback.message.edit_text(
            "📋 У вас пока нет бронирований.\n\n"
            "Хотите записаться?",
            reply_markup=get_main_menu()
        )
        return
    
    status_emojis = {
        "new": "🆕 Новое",
        "confirmed": "✅ Подтверждено",
        "cancelled": "❌ Отменено"
    }
    
    service_names = {
        "семейная": "👨‍👩‍👧 Семейная",
        "портрет": "📷 Портрет",
        "свадьба": "💒 Свадьба"
    }
    
    time_display = {
        "10:00": "10:00-12:00",
        "14:00": "14:00-16:00",
        "18:00": "18:00-20:00"
    }
    
    bookings_text = "📋 Ваши бронирования:\n\n"
    for booking in bookings:
        bookings_text += (
            f"#{booking['id']} - {service_names.get(booking['service'], booking['service'])}\n"
            f"📅 {booking['date']} 🕐 {time_display.get(booking['time_slot'], booking['time_slot'])}\n"
            f"{status_emojis.get(booking['status'], booking['status'])}\n\n"
        )
    
    await callback.message.edit_text(
        bookings_text,
        reply_markup=get_back_to_main_keyboard()
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message, db: Database):
    """
    Админ-панель для управления бронированиями.
    Доступна только для PHOTO_ADMIN_ID.
    """
    if message.from_user.id != PHOTO_ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return
    
    bookings = await db.get_all_bookings()
    
    if not bookings:
        await message.answer(
            "📋 Нет активных бронирований.",
            reply_markup=get_admin_bookings_keyboard([])
        )
        return
    
    await message.answer(
        "👑 Панель администратора\n\n"
        f"Всего бронирований: {len(bookings)}",
        reply_markup=get_admin_bookings_keyboard(bookings)
    )


@router.callback_query(F.data == "admin_refresh")
async def admin_refresh(callback: CallbackQuery, db: Database):
    """
    Обновление списка бронирований в админ-панели.
    """
    if callback.from_user.id != PHOTO_ADMIN_ID:
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    bookings = await db.get_all_bookings()
    
    await callback.message.edit_text(
        "👑 Панель администратора\n\n"
        f"Всего бронирований: {len(bookings)}",
        reply_markup=get_admin_bookings_keyboard(bookings)
    )
    await callback.answer("🔄 Список обновлен")


@router.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm_booking(callback: CallbackQuery, db: Database, bot: Any):
    """
    Подтверждение бронирования админом.
    """
    if callback.from_user.id != PHOTO_ADMIN_ID:
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    booking_id = int(callback.data.split("_")[2])
    
    success = await db.update_status(booking_id, "confirmed")
    
    if success:
        booking = await db.get_booking_by_id(booking_id)
        if booking:
            # Уведомление пользователя
            try:
                await bot.send_message(
                    chat_id=booking["user_id"],
                    text=f"✅ Ваше бронирование #{booking_id} подтверждено!\n\n"
                         f"Дата: {booking['date']}\n"
                         f"Время: {booking['time_slot']}\n\n"
                         "Ждем вас на фотосессии!"
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления пользователю: {e}")
        
        await callback.answer("✅ Бронирование подтверждено", show_alert=True)
        
        # Обновление списка
        bookings = await db.get_all_bookings()
        await callback.message.edit_text(
            "👑 Панель администратора\n\n"
            f"Всего бронирований: {len(bookings)}",
            reply_markup=get_admin_bookings_keyboard(bookings)
        )
    else:
        await callback.answer("❌ Ошибка обновления статуса", show_alert=True)


@router.callback_query(F.data.startswith("admin_cancel_"))
async def admin_cancel_booking(callback: CallbackQuery, db: Database, bot: Any):
    """
    Отмена бронирования админом.
    """
    if callback.from_user.id != PHOTO_ADMIN_ID:
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    booking_id = int(callback.data.split("_")[2])
    
    success = await db.update_status(booking_id, "cancelled")
    
    if success:
        booking = await db.get_booking_by_id(booking_id)
        if booking:
            # Уведомление пользователя
            try:
                await bot.send_message(
                    chat_id=booking["user_id"],
                    text=f"❌ Ваше бронирование #{booking_id} отменено.\n\n"
                         "Свяжитесь с нами для уточнения деталей."
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления пользователю: {e}")
        
        await callback.answer("❌ Бронирование отменено", show_alert=True)
        
        # Обновление списка
        bookings = await db.get_all_bookings()
        await callback.message.edit_text(
            "👑 Панель администратора\n\n"
            f"Всего бронирований: {len(bookings)}",
            reply_markup=get_admin_bookings_keyboard(bookings)
        )
    else:
        await callback.answer("❌ Ошибка обновления статуса", show_alert=True)


@router.callback_query(F.data.startswith("booking_info_"))
async def show_booking_info(callback: CallbackQuery, db: Database):
    """
    Показывает детальную информацию о бронировании (для информационных кнопок).
    """
    booking_id = int(callback.data.split("_")[2])
    booking = await db.get_booking_by_id(booking_id)
    
    if not booking:
        await callback.answer("❌ Бронирование не найдено", show_alert=True)
        return
    
    status_text = {
        "new": "🆕 Новое",
        "confirmed": "✅ Подтверждено",
        "cancelled": "❌ Отменено"
    }
    
    service_names = {
        "семейная": "👨‍👩‍👧 Семейная фотосессия",
        "портрет": "📷 Портретная фотосессия",
        "свадьба": "💒 Свадебная фотосессия"
    }
    
    time_display = {
        "10:00": "10:00-12:00",
        "14:00": "14:00-16:00",
        "18:00": "18:00-20:00"
    }
    
    info_text = (
        f"📋 Бронирование #{booking_id}\n\n"
        f"👤 Пользователь: {booking['user_name']}\n"
        f"🆔 ID: {booking['user_id']}\n"
        f"📸 Услуга: {service_names.get(booking['service'], booking['service'])}\n"
        f"📅 Дата: {booking['date']}\n"
        f"🕐 Время: {time_display.get(booking['time_slot'], booking['time_slot'])}\n"
        f"📊 Статус: {status_text.get(booking['status'], booking['status'])}"
    )
    
    await callback.answer(info_text, show_alert=True)
