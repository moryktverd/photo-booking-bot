import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import gallery, admin, booking, price, reviews
from config import ADMINS, PHOTOGRAPHERS

# Проверка токена
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в .env файле!")
    print("💡 Создайте файл .env с содержимым:")
    print("   BOT_TOKEN=ваш_токен_от_botfather")
    exit(1)

if "xxxxx" in BOT_TOKEN or len(BOT_TOKEN) < 40:
    print("❌ ОШИБКА: BOT_TOKEN содержит placeholder или невалидный!")
    print("💡 Замените токен в .env файле на реальный от @BotFather")
    print(f"   Текущий токен: {BOT_TOKEN[:20]}...")
    exit(1)

# Инициализация бота и диспетчера
try:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
except Exception as e:
    print(f"❌ Ошибка инициализации бота: {e}")
    print("💡 Проверьте, что токен в .env файле правильный!")
    exit(1)

# Обработчик команды /start
@dp.message(lambda message: message.text == "/start")
async def cmd_start(message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Запись", callback_data="booking")],
        [InlineKeyboardButton(text="💵 Прайс", callback_data="price")],
        [InlineKeyboardButton(text="⭐ Отзывы", callback_data="reviews")],
        [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_bookings")],
        [InlineKeyboardButton(text="📸 Галерея", callback_data="gallery")]
    ])
    await message.answer(
        "🎉 Photo Booking Bot готов!\n📸 Фотограф Тверь",
        reply_markup=keyboard
    )

# Обработчик возврата в главное меню
@dp.callback_query(lambda c: c.data == "main_menu")
async def back_to_main(callback):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Запись", callback_data="booking")],
        [InlineKeyboardButton(text="💵 Прайс", callback_data="price")],
        [InlineKeyboardButton(text="⭐ Отзывы", callback_data="reviews")],
        [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_bookings")],
        [InlineKeyboardButton(text="📸 Галерея", callback_data="gallery")]
    ])
    await callback.message.edit_text(
        "🎉 Photo Booking Bot готов!\n📸 Фотограф Тверь",
        reply_markup=keyboard
    )
    await callback.answer()

# Регистрация роутеров
dp.include_router(booking.router)
dp.include_router(gallery.router)
dp.include_router(admin.router)
dp.include_router(price.router)
dp.include_router(reviews.router)

# Запуск бота
async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
