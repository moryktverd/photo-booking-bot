import json
from pathlib import Path
from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.filters import Command
from config import ADMINS, PHOTOGRAPHERS

router = Router()

# FSM состояния для отзывов
class ReviewStates(StatesGroup):
    waiting_photographer = State()  # Ожидание выбора фотографа
    waiting_rating = State()        # Ожидание оценки (1-5)
    waiting_text = State()          # Ожидание текста отзыва

# Файл для хранения отзывов
REVIEWS_FILE = Path("data/reviews.json")

# Загрузка отзывов из файла
def load_reviews():
    """Загружает отзывы из JSON файла"""
    if REVIEWS_FILE.exists():
        with open(REVIEWS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Сохранение отзывов в файл
def save_reviews(reviews):
    """Сохраняет отзывы в JSON файл"""
    REVIEWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)

# Добавление отзыва
def add_review(user_id: int, user_name: str, photographer_id: str, rating: int, text: str):
    """Добавляет новый отзыв"""
    reviews = load_reviews()
    review = {
        "id": len(reviews) + 1,
        "user_id": user_id,
        "user_name": user_name,
        "photographer_id": photographer_id,
        "rating": rating,
        "text": text,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    reviews.append(review)
    save_reviews(reviews)
    return review

# Получение рейтинга фотографа
def get_photographer_rating(photographer_id: str):
    """Вычисляет средний рейтинг фотографа"""
    reviews = load_reviews()
    photographer_reviews = [r for r in reviews if r.get("photographer_id") == photographer_id]
    
    if not photographer_reviews:
        return 0.0, 0
    
    total_rating = sum(r["rating"] for r in photographer_reviews)
    average_rating = total_rating / len(photographer_reviews)
    return round(average_rating, 1), len(photographer_reviews)

# Получение последних отзывов
def get_latest_reviews(limit=5):
    """Возвращает последние N отзывов"""
    reviews = load_reviews()
    return sorted(reviews, key=lambda x: x.get("id", 0), reverse=True)[:limit]

# Обработчик кнопки "⭐ Отзывы"
@router.callback_query(F.data == "reviews")
async def show_reviews(callback: CallbackQuery):
    """Отображение отзывов"""
    reviews = get_latest_reviews(5)
    
    if not reviews:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Оставить отзыв", callback_data="add_review")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text(
            "⭐ Отзывы\n\n"
            "Пока нет отзывов. Будьте первым!",
            reply_markup=keyboard
        )
        await callback.answer()
        return
    
    # Вычисляем общий рейтинг
    all_ratings = [r["rating"] for r in reviews]
    overall_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0
    
    # Формируем текст с отзывами
    reviews_text = f"⭐ Отзывы\n\n★ {overall_rating:.1f} ({len(reviews)} отзывов)\n\n"
    
    for review in reviews:
        photographer_name = PHOTOGRAPHERS.get(
            review.get("photographer_id", ""), 
            {}
        ).get("name", "Неизвестный фотограф")
        
        stars = "★" * review["rating"] + "☆" * (5 - review["rating"])
        date = review.get("date", "").split()[0] if review.get("date") else ""
        
        reviews_text += (
            f"📸 {photographer_name}\n"
            f"{stars} ({review['rating']}/5)\n"
            f"👤 {review.get('user_name', 'Пользователь')}\n"
            f"💬 {review.get('text', '')}\n"
            f"📅 {date}\n\n"
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Оставить отзыв", callback_data="add_review")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        reviews_text,
        reply_markup=keyboard
    )
    await callback.answer()

# Начало добавления отзыва
@router.callback_query(F.data == "add_review")
async def start_add_review(callback: CallbackQuery, state: FSMContext):
    """Начало процесса добавления отзыва"""
    await state.set_state(ReviewStates.waiting_photographer)
    
    # Кнопки выбора фотографа
    keyboard_buttons = []
    for photographer_id, photographer_data in PHOTOGRAPHERS.items():
        rating, count = get_photographer_rating(photographer_id)
        rating_text = f" ★{rating}" if rating > 0 else ""
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📸 {photographer_data['name']}{rating_text}",
                callback_data=f"review_photographer_{photographer_id}"
            )
        ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="reviews")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        "⭐ Оставить отзыв\n\n"
        "Выберите фотографа:",
        reply_markup=keyboard
    )
    await callback.answer()

# Выбор фотографа для отзыва
@router.callback_query(ReviewStates.waiting_photographer, F.data.startswith("review_photographer_"))
async def select_review_photographer(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора фотографа"""
    photographer_id = callback.data.replace("review_photographer_", "")
    
    if photographer_id not in PHOTOGRAPHERS:
        await callback.answer("❌ Фотограф не найден!", show_alert=True)
        return
    
    await state.update_data(photographer_id=photographer_id)
    await state.set_state(ReviewStates.waiting_rating)
    
    # Кнопки выбора рейтинга
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐", callback_data="rating_1"),
            InlineKeyboardButton(text="⭐⭐", callback_data="rating_2"),
            InlineKeyboardButton(text="⭐⭐⭐", callback_data="rating_3"),
        ],
        [
            InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rating_4"),
            InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rating_5"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="add_review")]
    ])
    
    photographer_name = PHOTOGRAPHERS[photographer_id]["name"]
    
    await callback.message.edit_text(
        f"⭐ Оцените фотографа\n\n"
        f"📸 {photographer_name}\n\n"
        f"Выберите оценку (1-5 звезд):",
        reply_markup=keyboard
    )
    await callback.answer()

# Выбор рейтинга
@router.callback_query(ReviewStates.waiting_rating, F.data.startswith("rating_"))
async def select_rating(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора рейтинга"""
    rating = int(callback.data.replace("rating_", ""))
    
    await state.update_data(rating=rating)
    await state.set_state(ReviewStates.waiting_text)
    
    await callback.message.edit_text(
        f"⭐ Напишите отзыв\n\n"
        f"Вы выбрали: {'⭐' * rating}\n\n"
        f"Оставьте ваш отзыв (текстом):"
    )
    await callback.answer()

# Получение текста отзыва
@router.message(ReviewStates.waiting_text)
async def get_review_text(message: Message, state: FSMContext):
    """Обработка текста отзыва"""
    text = message.text.strip()
    
    if len(text) < 3:
        await message.answer("❌ Отзыв слишком короткий! Напишите минимум 3 символа.")
        return
    
    if len(text) > 500:
        await message.answer("❌ Отзыв слишком длинный! Максимум 500 символов.")
        return
    
    data = await state.get_data()
    photographer_id = data.get("photographer_id")
    rating = data.get("rating")
    
    user_id = message.from_user.id
    user_name = message.from_user.full_name or message.from_user.username or "Пользователь"
    
    # Сохраняем отзыв
    review = add_review(user_id, user_name, photographer_id, rating, text)
    
    photographer_name = PHOTOGRAPHERS[photographer_id]["name"]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Посмотреть все отзывы", callback_data="reviews")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    await message.answer(
        f"✅ Спасибо за отзыв!\n\n"
        f"📸 Фотограф: {photographer_name}\n"
        f"{'⭐' * rating}\n"
        f"💬 {text}\n\n"
        f"Ваш отзыв добавлен!",
        reply_markup=keyboard
    )
    
    await state.clear()

# Админ-команда для добавления отзыва
@router.message(Command("add_review"))
async def cmd_add_review(message: Message):
    """Команда для админа: /add_review photographer_id "текст отзыва\""""
    if message.from_user.id not in ADMINS:
        await message.answer("❌ У вас нет прав администратора!")
        return
    
    # Парсинг команды: /add_review anna "Огонь! 5⭐"
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            "📋 Использование команды:\n"
            "/add_review <photographer_id> \"текст отзыва\"\n\n"
            "Пример:\n"
            '/add_review anna "Огонь! 5⭐"'
        )
        return
    
    photographer_id = args[1]
    text = args[2].strip('"\'')  # Убираем кавычки
    
    if photographer_id not in PHOTOGRAPHERS:
        await message.answer(
            f"❌ Фотограф '{photographer_id}' не найден!\n\n"
            f"Доступные фотографы: {', '.join(PHOTOGRAPHERS.keys())}"
        )
        return
    
    # Извлекаем рейтинг из текста (ищем число 1-5)
    rating = 5  # По умолчанию
    if "5" in text or "⭐⭐⭐⭐⭐" in text:
        rating = 5
    elif "4" in text or "⭐⭐⭐⭐" in text:
        rating = 4
    elif "3" in text or "⭐⭐⭐" in text:
        rating = 3
    elif "2" in text or "⭐⭐" in text:
        rating = 2
    elif "1" in text or "⭐" in text:
        rating = 1
    
    user_id = message.from_user.id
    user_name = message.from_user.full_name or "Администратор"
    
    # Сохраняем отзыв
    review = add_review(user_id, user_name, photographer_id, rating, text)
    
    photographer_name = PHOTOGRAPHERS[photographer_id]["name"]
    
    await message.answer(
        f"✅ Отзыв добавлен!\n\n"
        f"📸 Фотограф: {photographer_name}\n"
        f"{'⭐' * rating}\n"
        f"💬 {text}"
    )
