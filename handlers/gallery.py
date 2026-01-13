import json
from pathlib import Path
from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile, InputMediaPhoto
from config import PHOTOGRAPHERS

router = Router()

# Обработчик callback "gallery" - выбор фотографа
@router.callback_query(F.data == "gallery")
async def show_gallery(callback: CallbackQuery):
    # Создаем кнопки для каждого фотографа
    keyboard_buttons = []
    for photographer_id, photographer_data in PHOTOGRAPHERS.items():
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📸 {photographer_data['name']}", 
                callback_data=f"gallery_{photographer_id}"
            )
        ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(
        "📸 Галерея фотографий\n\nВыберите фотографа:",
        reply_markup=keyboard
    )
    await callback.answer()

# Динамическая галерея для конкретного фотографа
@router.callback_query(F.data.startswith("gallery_"))
async def gallery(callback: CallbackQuery):
    # Извлекаем photographer_id из callback_data
    photographer_id = callback.data.replace("gallery_", "")
    
    # Проверяем существование фотографа
    if photographer_id not in PHOTOGRAPHERS:
        await callback.answer("❌ Фотограф не найден!", show_alert=True)
        return
    
    photographer_name = PHOTOGRAPHERS[photographer_id]["name"]
    portfolio_path = Path(f"data/{photographer_id}/portfolio.json")
    
    # Проверяем наличие portfolio.json
    if not portfolio_path.exists():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к галерее", callback_data="gallery")]
        ])
        await callback.message.edit_text(
            f"📸 {photographer_name}\n\n"
            f"❌ Портфолио пока пустое. Фотографии будут добавлены администратором.",
            reply_markup=keyboard
        )
        await callback.answer()
        return
    
    # Загружаем portfolio
    try:
        with open(portfolio_path, 'r', encoding='utf-8') as f:
            portfolio = json.load(f)
        
        photos = portfolio.get("photos", [])
        
        if not photos:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад к галерее", callback_data="gallery")]
            ])
            await callback.message.edit_text(
                f"📸 {photographer_name}\n\n"
                f"❌ Портфолио пока пустое.",
                reply_markup=keyboard
            )
            await callback.answer()
            return
        
        # Удаляем старое сообщение
        await callback.message.delete()
        
        # Отправляем первое фото
        first_photo = photos[0]
        photo_path = Path(first_photo["path"])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data=f"photo_{photographer_id}_0_prev"),
                InlineKeyboardButton(
                    text=f"1/{len(photos)}", 
                    callback_data="photo_count"
                ),
                InlineKeyboardButton(text="➡️", callback_data=f"photo_{photographer_id}_0_next")
            ],
            [InlineKeyboardButton(text="🔙 Назад к галерее", callback_data="gallery")]
        ])
        
        if photo_path.exists():
            photo_file = FSInputFile(str(photo_path))
            await callback.bot.send_photo(
                chat_id=callback.from_user.id,
                photo=photo_file,
                caption=f"📸 {photographer_name}\n\n{first_photo.get('caption', '')}",
                reply_markup=keyboard
            )
        else:
            await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=f"📸 {photographer_name}\n\n{first_photo.get('caption', '')}\n\n❌ Файл не найден: {photo_path}",
                reply_markup=keyboard
            )
        
        await callback.answer()
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка загрузки портфолио: {e}", show_alert=True)

# Навигация по фото (следующее/предыдущее)
@router.callback_query(F.data.startswith("photo_"))
async def navigate_photo(callback: CallbackQuery):
    """Навигация по фотографиям в галерее"""
    parts = callback.data.split("_")
    if len(parts) < 4:
        await callback.answer("❌ Ошибка навигации", show_alert=True)
        return
    
    photographer_id = parts[1]
    current_index = int(parts[2])
    direction = parts[3]  # "next" или "prev"
    
    portfolio_path = Path(f"data/{photographer_id}/portfolio.json")
    if not portfolio_path.exists():
        await callback.answer("❌ Портфолио не найдено", show_alert=True)
        return
    
    with open(portfolio_path, 'r', encoding='utf-8') as f:
        portfolio = json.load(f)
    
    photos = portfolio.get("photos", [])
    if not photos:
        await callback.answer("❌ Нет фотографий", show_alert=True)
        return
    
    # Вычисляем новый индекс
    if direction == "next":
        new_index = (current_index + 1) % len(photos)
    else:  # prev
        new_index = (current_index - 1) % len(photos)
    
    photo = photos[new_index]
    photo_path = Path(photo["path"])
    photographer_name = PHOTOGRAPHERS[photographer_id]["name"]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"photo_{photographer_id}_{new_index}_prev"),
            InlineKeyboardButton(
                text=f"{new_index + 1}/{len(photos)}", 
                callback_data="photo_count"
            ),
            InlineKeyboardButton(text="➡️", callback_data=f"photo_{photographer_id}_{new_index}_next")
        ],
        [InlineKeyboardButton(text="🔙 Назад к галерее", callback_data="gallery")]
    ])
    
    try:
        if photo_path.exists():
            photo_file = FSInputFile(str(photo_path))
            await callback.message.edit_media(
                media=InputMediaPhoto(
                    media=photo_file,
                    caption=f"📸 {photographer_name}\n\n{photo.get('caption', '')}"
                ),
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_caption(
                caption=f"📸 {photographer_name}\n\n{photo.get('caption', '')}\n\n❌ Файл не найден: {photo_path}",
                reply_markup=keyboard
            )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
