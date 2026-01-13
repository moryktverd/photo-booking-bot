import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router
from config import BOT_TOKEN
from database import Database
from middleware import DatabaseMiddleware

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация базы данных
    db = Database("bookings.db")
    await db.create_table()
    
    # Регистрация middleware
    dp.message.middleware(DatabaseMiddleware(db))
    dp.callback_query.middleware(DatabaseMiddleware(db))
    
    # Регистрация роутера
    dp.include_router(router)
    
    # Запуск бота
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
