# Photo Booking Bot

Telegram-бот для бронирования фотосессий. Полнофункциональный бот с админ-панелью для управления записями.

## Компоненты

- **database.py** - модуль для работы с базой данных (aiosqlite)
- **keyboards.py** - модуль с InlineKeyboardMarkup для интерфейса бота
- **states.py** - FSM состояния для процесса бронирования
- **middleware.py** - middleware для предоставления доступа к БД
- **handlers.py** - обработчики команд и callback-запросов
- **bot.py** - точка входа для запуска бота
- **config.py** - конфигурация (токен бота и ID администратора)

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

1. Создайте файл `.env` на основе `env.example`:
```bash
cp env.example .env
```

2. Откройте `.env` и укажите:
   - `BOT_TOKEN` - получите токен у [@BotFather](https://t.me/BotFather) в Telegram
   - `ADMIN_ID` - ваш Telegram ID (можно узнать у [@userinfobot](https://t.me/userinfobot))

Пример `.env`:
```
BOT_TOKEN=твой_токен
ADMIN_ID=123456789  # твой Telegram ID
```

3. Запустите бота:
```bash
python bot.py
```

## Функциональность

### Команды

- `/start` - главное меню бота
- `/admin` - панель администратора (только для администратора)

### Процесс бронирования

1. Пользователь нажимает "📸 Записаться"
2. Выбирает услугу (семейная/портрет/свадьба)
3. Вводит дату в формате YYYY-MM-DD
4. Выбирает временной слот (10:00-12:00, 14:00-16:00, 18:00-20:00)
5. Подтверждает бронирование
6. Бронирование сохраняется в БД с статусом "new"
7. Администратор получает уведомление о новом бронировании

### Админ-панель

- Просмотр всех бронирований
- Подтверждение бронирований (статус → "confirmed")
- Отмена бронирований (статус → "cancelled")
- Автоматическая отправка уведомлений пользователям при изменении статуса

## Использование

```python
import asyncio
from database import Database

async def main():
    # Создание экземпляра базы данных
    db = Database("bookings.db")
    
    # Создание таблицы
    await db.create_table()
    
    # Добавление бронирования
    booking_id = await db.add_booking(
        user_id=123456789,
        user_name="Иван Иванов",
        service="семейная",
        date="2024-12-25",
        time_slot="14:00",
        status="new"
    )
    
    # Получение бронирований пользователя
    user_bookings = await db.get_user_bookings(user_id=123456789)
    
    # Получение всех бронирований
    all_bookings = await db.get_all_bookings()
    
    # Обновление статуса
    await db.update_status(booking_id=1, status="confirmed")

if __name__ == "__main__":
    asyncio.run(main())
```

## Структура таблицы bookings

- `id` - INTEGER PRIMARY KEY (автоинкремент)
- `user_id` - INTEGER (ID пользователя Telegram)
- `user_name` - TEXT (имя пользователя)
- `service` - TEXT (семейная/портрет/свадьба)
- `date` - TEXT (формат YYYY-MM-DD)
- `time_slot` - TEXT (10:00/14:00/18:00)
- `status` - TEXT (new/confirmed/cancelled, по умолчанию 'new')

## Методы класса Database

- `create_table()` - создание таблицы bookings
- `add_booking(user_id, user_name, service, date, time_slot, status='new')` - добавление бронирования
- `get_user_bookings(user_id)` - получение всех бронирований пользователя
- `get_all_bookings()` - получение всех бронирований
- `update_status(booking_id, status)` - обновление статуса бронирования
- `get_booking_by_id(booking_id)` - получение бронирования по ID (дополнительный метод)

## Клавиатуры (keyboards.py)

### Основные функции

- `get_main_menu()` - главное меню с кнопками "📸 Записаться", "📋 Мои записи", "ℹ️ Услуги"
- `get_services_keyboard()` - выбор услуги с ценами
- `get_time_slots_keyboard(date, service)` - выбор временного слота для даты
- `get_confirm_booking_keyboard(booking_id)` - подтверждение бронирования
- `get_admin_bookings_keyboard(bookings)` - админ-панель со списком записей
- `get_back_to_main_keyboard()` - кнопка возврата в главное меню
- `get_services_info_keyboard()` - меню после просмотра услуг

### Пример использования клавиатур

```python
from aiogram import Bot
from keyboards import get_main_menu, get_services_keyboard, get_time_slots_keyboard

# Отправка главного меню
await bot.send_message(
    chat_id=user_id,
    text="Добро пожаловать! Выберите действие:",
    reply_markup=get_main_menu()
)

# Отправка меню услуг
await bot.send_message(
    chat_id=user_id,
    text="Выберите услугу:",
    reply_markup=get_services_keyboard()
)

# Отправка временных слотов
await bot.send_message(
    chat_id=user_id,
    text="Выберите время:",
    reply_markup=get_time_slots_keyboard(date="2024-12-25", service="семейная")
)

# Админ-панель
from database import Database
db = Database()
bookings = await db.get_all_bookings()
await bot.send_message(
    chat_id=admin_id,
    text="Список всех записей:",
    reply_markup=get_admin_bookings_keyboard(bookings)
)
```

### Callback данные

- `book_service` - начало записи
- `my_bookings` - просмотр своих записей
- `services_info` - информация об услугах
- `service_{название}` - выбор услуги (например, `service_семейная`)
- `timeslot_{date}_{time}_{service}` - выбор временного слота
- `confirm_booking_{id}` - подтверждение бронирования
- `admin_confirm_{id}` - подтверждение записи админом
- `admin_cancel_{id}` - отмена записи админом
- `back_to_main` - возврат в главное меню

## FSM Состояния (states.py)

### BookingStates

Класс состояний для управления процессом бронирования через Finite State Machine (FSM):

- `waiting_service` - ожидание выбора услуги пользователем
- `waiting_date` - ожидание ввода даты фотосессии
- `waiting_time` - ожидание выбора временного слота
- `confirm` - ожидание подтверждения бронирования

### Пример использования FSM

```python
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from states import BookingStates
from keyboards import get_services_keyboard

router = Router()

@router.callback_query(F.data == "book_service")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    """Начало процесса бронирования"""
    await state.set_state(BookingStates.waiting_service)
    await callback.message.answer(
        "Выберите услугу:",
        reply_markup=get_services_keyboard()
    )

@router.callback_query(F.data.startswith("service_"))
async def select_service(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора услуги"""
    service = callback.data.split("_")[1]
    await state.update_data(service=service)
    await state.set_state(BookingStates.waiting_date)
    await callback.message.answer("Введите дату в формате YYYY-MM-DD:")

@router.message(BookingStates.waiting_date)
async def process_date(message: Message, state: FSMContext):
    """Обработка ввода даты"""
    date = message.text
    # Валидация даты здесь
    await state.update_data(date=date)
    await state.set_state(BookingStates.waiting_time)
    # Показать клавиатуру с временными слотами

@router.callback_query(BookingStates.waiting_time, F.data.startswith("timeslot_"))
async def select_time(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    # Парсинг callback_data и сохранение времени
    await state.set_state(BookingStates.confirm)
    # Показать подтверждение бронирования
```

# фотобукинг-бот
