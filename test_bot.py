import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
print(f"TOKEN OK: {len(TOKEN) == 46}")

bot = Bot(token=TOKEN)
