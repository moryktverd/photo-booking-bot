import asyncio
import json
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMINS, PHOTOGRAPHERS

router = Router()

# Хранилище для ожидаемых фото (user_id: {photographer_id, caption})
pending_photos = {}

# Функция для обновления portfolio.json
async def update_portfolio(photographer_id: str, photo_path: str, caption: str):
    """Обновляет portfolio.json для фотографа"""
    portfolio_path = Path(f"data/{photographer_id}/portfolio.json")
    portfolio_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Загружаем существующий portfolio или создаем новый
    if portfolio_path.exists():
        with open(portfolio_path, 'r', encoding='utf-8') as f:
            portfolio = json.load(f)
    else:
        portfolio = {
            "photographer_id": photographer_id,
            "name": PHOTOGRAPHERS.get(photographer_id, {}).get("name", "Unknown"),
            "photos": []
        }
    
    # Добавляем новое фото
    portfolio["photos"].append({
        "path": photo_path,
        "caption": caption,
        "added_at": str(asyncio.get_event_loop().time())
    })
    
    # Сохраняем обновленный portfolio
    with open(portfolio_path, 'w', encoding='utf-8') as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)
    
    return portfolio

# Админ-панель: команда добавления фото
@router.message(Command("admin_add_photo"))
async def cmd_admin_add_photo(message: Message):
    """Команда для добавления фото фотографу"""
    # Проверка прав администратора
    if message.from_user.id not in ADMINS:
        await message.answer("❌ У вас нет прав администратора!")
        return
    
    # Парсинг команды: /admin_add_photo <photographer_id> <caption>
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            "📋 Использование команды:\n"
            "/admin_add_photo <photographer_id> <caption>\n\n"
            "Пример:\n"
            "/admin_add_photo anna Портретная фотосессия в студии"
        )
        return
    
    photographer_id = args[1]
    caption = args[2]
    
    # Проверка существования фотографа
    if photographer_id not in PHOTOGRAPHERS:
        await message.answer(
            f"❌ Фотограф '{photographer_id}' не найден!\n\n"
            f"Доступные фотографы: {', '.join(PHOTOGRAPHERS.keys())}"
        )
        return
    
    # Сохраняем в ожидании фото
    pending_photos[message.from_user.id] = {
        "photographer_id": photographer_id,
        "caption": caption
    }
    
    await message.answer(
        f"📸 Готов к загрузке фото для {PHOTOGRAPHERS[photographer_id]['name']}\n"
        f"📝 Подпись: {caption}\n\n"
        f"Отправьте фото..."
    )

# Обработчик получения фото от админа
@router.message(F.photo, F.from_user.id.in_(ADMINS))
async def handle_admin_photo(message: Message):
    """Обработка фото от администратора"""
    if message.from_user.id not in pending_photos:
        return  # Фото не ожидается
    
    data = pending_photos[message.from_user.id]
    photographer_id = data["photographer_id"]
    caption = data["caption"]
    
    try:
        # Получаем файл фото
        photo = message.photo[-1]  # Берем самое большое разрешение
        file_info = await message.bot.get_file(photo.file_id)
        
        # Создаем директорию для фотографа
        photo_dir = Path(f"data/{photographer_id}/photos")
        photo_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем имя файла
        file_extension = file_info.file_path.split('.')[-1]
        photo_count = len(list(photo_dir.glob("*"))) + 1
        photo_filename = f"photo_{photo_count}.{file_extension}"
        photo_path = photo_dir / photo_filename
        
        # Скачиваем и сохраняем фото
        await message.bot.download_file(file_info.file_path, photo_path)
        
        # Обновляем portfolio.json
        relative_path = f"data/{photographer_id}/photos/{photo_filename}"
        portfolio = await update_portfolio(photographer_id, relative_path, caption)
        
        # Удаляем из ожидающих
        del pending_photos[message.from_user.id]
        
        await message.answer(
            f"✅ Фото успешно добавлено!\n\n"
            f"👤 Фотограф: {PHOTOGRAPHERS[photographer_id]['name']}\n"
            f"📝 Подпись: {caption}\n"
            f"📁 Путь: {relative_path}\n"
            f"📊 Всего фото: {len(portfolio['photos'])}"
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении фото: {e}")
        if message.from_user.id in pending_photos:
            del pending_photos[message.from_user.id]

# Файл для хранения записей
APPOINTMENTS_FILE = Path("data/appointments.json")

# Загрузка записей
def load_appointments():
    """Загружает записи из JSON файла"""
    if APPOINTMENTS_FILE.exists():
        with open(APPOINTMENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Команда /admin_calendar - показать все записи
@router.message(Command("admin_calendar"))
async def cmd_admin_calendar(message: Message):
    """Показать календарь всех записей для админа"""
    if message.from_user.id not in ADMINS:
        await message.answer("❌ У вас нет прав администратора!")
        return
    
    appointments = load_appointments()
    
    if not appointments:
        await message.answer(
            "📅 Календарь записей\n\n"
            "❌ Нет записей"
        )
        return
    
    # Группируем записи по дате
    appointments_by_date = {}
    for appt in appointments:
        date = appt.get("date", "")
        if date not in appointments_by_date:
            appointments_by_date[date] = []
        appointments_by_date[date].append(appt)
    
    # Сортируем даты
    sorted_dates = sorted(appointments_by_date.keys())
    
    # Формируем текст
    calendar_text = "📅 Календарь записей\n\n"
    
    days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    for date_str in sorted_dates:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = days_ru[date_obj.weekday()]
        date_display = date_obj.strftime(f"%d.%m.%Y ({day_name})")
        
        calendar_text += f"📅 {date_display}\n"
        
        for appt in appointments_by_date[date_str]:
            photographer_name = appt.get("photographer_name", "Unknown")
            time_slot = appt.get("time_slot", "")
            user_name = appt.get("user_name", "Пользователь")
            status = appt.get("status", "new")
            
            status_emoji = {
                "new": "🆕",
                "confirmed": "✅",
                "cancelled": "❌"
            }.get(status, "❓")
            
            time_display = {
                "10:00": "10:00-12:00",
                "14:00": "14:00-16:00",
                "18:00": "18:00-20:00"
            }.get(time_slot, time_slot)
            
            calendar_text += (
                f"  {status_emoji} {time_display} - {photographer_name}\n"
                f"     👤 {user_name}\n"
            )
        
        calendar_text += "\n"
    
    await message.answer(calendar_text)
