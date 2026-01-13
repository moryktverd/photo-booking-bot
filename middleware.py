from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from database import Database


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для предоставления доступа к базе данных в обработчиках.
    """
    
    def __init__(self, db: Database):
        """
        Инициализация middleware.
        
        Args:
            db: Экземпляр класса Database
        """
        self.db = db
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обработка события с добавлением БД в data.
        
        Args:
            handler: Обработчик события
            event: Событие Telegram
            data: Словарь с данными для обработчика
        
        Returns:
            Результат выполнения обработчика
        """
        data["db"] = self.db
        return await handler(event, data)
