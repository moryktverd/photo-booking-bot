from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Записаться", callback_data="book")],
        [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_bookings")],
        [InlineKeyboardButton(text="ℹ️ Услуги", callback_data="services")]
    ])
    return kb

def services_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍👩‍👧 Семейная (5000₽)", callback_data="service_family")],
        [InlineKeyboardButton(text="📷 Портрет (3000₽)", callback_data="service_portrait")],
        [InlineKeyboardButton(text="💒 Свадьба (15000₽)", callback_data="service_wedding")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main")]
    ])
    return kb
