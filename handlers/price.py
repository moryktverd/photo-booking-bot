from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router()

# Прайс-лист услуг
PRICES = {
    "family": {
        "name": "👨‍👩‍👧 Семейная фотосессия",
        "price": 5000,
        "duration": "1-2 часа",
        "description": "Семейная фотосессия на природе или в студии. 30+ обработанных фото"
    },
    "portrait": {
        "name": "📷 Портретная фотосессия",
        "price": 3000,
        "duration": "1 час",
        "description": "Индивидуальные портреты в студии или на локации. 20+ обработанных фото"
    },
    "wedding": {
        "name": "💒 Свадебная фотосессия",
        "price": 15000,
        "duration": "Весь день",
        "description": "Полное сопровождение свадьбы. 200+ обработанных фото, фотоальбом"
    }
}

# Обработчик кнопки "ℹ️ Прайс" или "💵 Услуги и цены"
@router.callback_query(F.data == "price")
async def show_price(callback: CallbackQuery):
    """Отображение прайс-листа"""
    price_text = "💵 Прайс-лист услуг\n\n"
    
    for service_key, service_data in PRICES.items():
        price_text += (
            f"{service_data['name']}\n"
            f"💰 {service_data['price']}₽\n"
            f"⏱ {service_data['duration']}\n"
            f"📝 {service_data['description']}\n\n"
        )
    
    price_text += "Выберите услугу для записи:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨‍👩‍👧 Семейная (5000₽)", callback_data="book_service_family"),
            InlineKeyboardButton(text="📷 Портрет (3000₽)", callback_data="book_service_portrait")
        ],
        [InlineKeyboardButton(text="💒 Свадьба (15000₽)", callback_data="book_service_wedding")],
        [InlineKeyboardButton(text="📅 Записаться", callback_data="booking")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        price_text,
        reply_markup=keyboard
    )
    await callback.answer()

# Обработчик выбора услуги из прайса
@router.callback_query(F.data.startswith("book_service_"))
async def book_from_price(callback: CallbackQuery):
    """Переход к записи после выбора услуги из прайса"""
    service_key = callback.data.replace("book_service_", "")
    
    if service_key in PRICES:
        service = PRICES[service_key]
        await callback.message.edit_text(
            f"✅ Выбрана услуга: {service['name']}\n"
            f"💰 Цена: {service['price']}₽\n\n"
            "Нажмите кнопку ниже для начала записи:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📅 Перейти к записи", callback_data="booking")],
                [InlineKeyboardButton(text="🔙 Назад к прайсу", callback_data="price")]
            ])
        )
        await callback.answer()
    else:
        await callback.answer("❌ Услуга не найдена", show_alert=True)
